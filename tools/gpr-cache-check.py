#!/usr/bin/env python3
"""Checks the generated units' register caching (the generator's --cache-gpr)
by abstract interpretation, independently of the generator's own dataflow.

In a leaf or call function with cached registers, guest register n lives in
the local r<n>; `r<n> = ctx.gpr[n];` loads it and `ctx.gpr[n] = r<n>;` stores
it. Per register the checker tracks two facts along every path:
  valid:   r<n> holds the register's current value
  current: ctx.gpr[n] holds the register's current value
and requires
  - a read of r<n>, and a store of it, only where it is valid;
  - a load only where the context is current;
  - every register current in the context wherever the function leaves or
    hands the context to other code (return, chained call, native fast path,
    rt.unsupported, ctx.execute_signed_add/sub);
  - no other mention of ctx.gpr in such a function.
At function entry, at a continuation case and after a call nothing is valid
and everything is current. Labels take the intersection over their incoming
paths (iterated to a fixed point).

  tools/gpr-cache-check.py <generated dir>     exit 1 on any violation
"""
import glob
import re
import sys

ALL = (1 << 32) - 1
FUNC = re.compile(r'^void (recomp_(?:fn|leaf)_[0-9A-F]{8})\(')
DECL = re.compile(r'^    std::uint32_t r\d+(?:, r\d+)*;$')
LABEL = re.compile(r'^(L_[0-9A-F]{8}):$')
LOAD = re.compile(r'^r(\d+) = ctx\.gpr\[(\d+)\]$')
STORE = re.compile(r'^ctx\.gpr\[(\d+)\] = r(\d+)$')
WRITE = re.compile(r'\br(\d+) = (?!=)')
REG = re.compile(r'\br(\d+)\b')
GOTO = re.compile(r'\bgoto (L_[0-9A-F]{8})$')
CALL = re.compile(r'invoke_chained|invoke_native_fast_path|recomp_(?:fn|leaf|unit)_\w+\(rt, ctx')
ADDSUB = re.compile(r'ctx\.execute_signed_(?:add|sub)\((\d+)u')
INLINE_IF = re.compile(r'^if \(.*\) \{ .* \}(?: \})*$')
ODD_WRITE = re.compile(r'\br\d+ (?:[-+*/|&^]|<<|>>)= |[&]r\d+\b(?! [&|])|\+\+r\d+|r\d+\+\+')


class State:
    __slots__ = ('valid', 'current')

    def __init__(self, valid=0, current=ALL):
        self.valid = valid
        self.current = current

    def copy(self):
        return State(self.valid, self.current)


def meet(a, b):
    if a is None:
        return None if b is None else b.copy()
    if b is None:
        return a.copy()
    return State(a.valid & b.valid, a.current & b.current)


def check_function(name, lines, errors):
    labels_in = {}
    changed = True

    def run(report):
        nonlocal changed
        state = State()
        stack = []          # ('fork', saved) or ('plain', None)
        jump_switch = None
        in_jump_switch = False

        def err(number, text, what):
            if report:
                errors.append(f'{name} line {number}: {what}: {text.strip()[:140]}')

        def flow(label):
            nonlocal changed
            old = labels_in.get(label)
            new = meet(old, state)
            if old is None or new.valid != old.valid or new.current != old.current:
                labels_in[label] = new
                changed = True

        for number, line in lines:
            text = line.strip()
            if not text or text.startswith('//'):
                continue
            label = LABEL.match(text)
            if label:
                if state is not None:
                    flow(label.group(1))
                known = labels_in.get(label.group(1))
                state = known.copy() if known is not None else None
                stack_depth_ok = not stack
                if not stack_depth_ok:
                    err(number, text, 'label inside a block')
                continue
            # A computed jump's switch over the function's blocks: every case
            # leaves with the state at the switch; after it, that state again.
            if text == 'switch (jump_target) {':
                jump_switch = state.copy() if state is not None else None
                in_jump_switch = True
                continue
            if in_jump_switch:
                if text.startswith('case '):
                    state = jump_switch.copy() if jump_switch is not None else None
                elif text == 'default: break;':
                    continue
                elif text == '}':
                    state = jump_switch
                    in_jump_switch = False
                    continue
            elif 'vfpu_rounded' in text and (text.startswith('case ') or text.startswith('default:')):
                # The rounding-mode switch inside a VFPU conversion: no
                # registers, not an entry of the function.
                continue
            elif text.startswith('case ') or text.startswith('default:'):
                state = State()
            if ODD_WRITE.search(text):
                err(number, text, 'register written in a form the checker does not know')
            opens = text.count('{') - text.count('{}')
            closes = text.count('}') - text.count('{}')
            net = opens - closes
            # `} else {`, `} else if (...) {`: no register writes in these arms.
            if text.startswith('}') and net == 0 and opens > 0:
                if WRITE.search(text):
                    err(number, text, 'register write on an else line')
                continue
            # A braced `if` on one line, `if (c) { a; b; }`: its body runs on
            # one path only; what follows the line is the meet of both paths.
            inline_if = INLINE_IF.match(text) if net <= 0 else None
            fork = net > 0 and text.startswith('if (')
            after_call = None

            def reads(expression):
                for match in REG.finditer(expression):
                    if not (state.valid >> int(match.group(1))) & 1:
                        err(number, text, f'r{match.group(1)} read while not valid')

            def hand_over(what):
                if state.current != ALL:
                    err(number, text, what + ' with registers not stored: %s' %
                        ' '.join(f'r{n}' for n in range(32) if not (state.current >> n) & 1))

            def statement(piece, conditional):
                nonlocal state
                if not piece or state is None:
                    return
                if 'ctx.gpr[' in piece and not LOAD.match(piece) and not STORE.match(piece):
                    err(number, text, 'context register access in a cached function')
                load = LOAD.match(piece)
                store = STORE.match(piece)
                if load:
                    n = int(load.group(1))
                    if n != int(load.group(2)):
                        err(number, text, 'load of another register')
                    if not (state.current >> n) & 1:
                        err(number, text, f'r{n} loaded while the context is stale')
                    state.valid |= 1 << n
                    return
                if store:
                    n = int(store.group(1))
                    if n != int(store.group(2)):
                        err(number, text, 'store of another register')
                    if not (state.valid >> n) & 1:
                        err(number, text, f'r{n} stored while not valid')
                    state.current |= 1 << n
                    return
                write = WRITE.match(piece)
                rest = piece[write.end():] if write else piece
                if WRITE.search(rest):
                    err(number, text, 'second register write in one statement')
                reads(rest)
                addsub = ADDSUB.search(piece)
                leaves = piece == 'return' or 'rt.unsupported(' in piece or 'rt.arithmetic_overflow(' in piece
                if CALL.search(piece) or addsub or leaves:
                    hand_over('context handed over')
                    if addsub:
                        state.valid &= ~(1 << int(addsub.group(1)))
                    elif not leaves:
                        state = State()
                if write:
                    n = int(write.group(1))
                    if conditional and not (state.valid >> n) & 1:
                        err(number, text, f'r{n} written conditionally while not valid')
                    state.valid |= 1 << n
                    state.current &= ~(1 << n)
                goto = GOTO.search(piece)
                if goto:
                    flow(goto.group(1))
                    state = None
                elif piece == 'return':
                    state = None

            def split_head(piece):
                depth = 0
                for index, char in enumerate(piece):
                    if char == '(':
                        depth += 1
                    elif char == ')':
                        depth -= 1
                        if depth == 0:
                            return piece[:index + 1], piece[index + 1:].strip()
                return piece, ''

            if inline_if is not None:
                if state is not None:
                    head, body = split_head(text)
                    reads(head)
                    if CALL.search(head):
                        hand_over('call')
                        state = State()
                    saved = state.copy()
                    for piece in body.split(';'):
                        statement(piece.strip().strip('{}').strip(), False)
                    state = meet(saved, state)
            else:
                for raw in text.split(';'):
                    piece = raw.strip()
                    while piece.startswith('{') or piece.startswith('}'):
                        piece = piece[1:].strip()
                    conditional = False
                    if piece.startswith('if ('):
                        head, piece = split_head(piece)
                        conditional = not piece.startswith('{')
                        while piece.startswith('{'):
                            piece = piece[1:].strip()
                        if state is not None:
                            reads(head)
                            if CALL.search(head):
                                err(number, text, 'call in an if the checker does not know')
                    elif piece.startswith('case ') or piece.startswith('default:'):
                        piece = piece.split(':', 1)[1].strip()
                        while piece.startswith('{'):
                            piece = piece[1:].strip()
                    statement(piece, conditional)
            if net > 0:
                for _ in range(net):
                    stack.append(('fork', state.copy() if state is not None else None) if fork else ('plain', None))
                    fork = False
            elif net < 0:
                for _ in range(-net):
                    if not stack:
                        break
                    kind, saved = stack.pop()
                    if kind == 'fork':
                        state = meet(saved, state) if (saved is not None or state is not None) else None
        return

    passes = 0
    while changed and passes < 200:
        changed = False
        run(False)
        passes += 1
    run(True)


def main():
    directory = sys.argv[1]
    errors = []
    functions = cached = 0
    for path in sorted(glob.glob(directory + '/generated_unit_*.cpp')):
        name = None
        body = []
        for number, line in enumerate(open(path), 1):
            line = line.rstrip('\n')
            start = FUNC.match(line)
            if start:
                name, body, is_cached = start.group(1), [], False
                continue
            if name is None:
                continue
            if line == '}':
                functions += 1
                if is_cached:
                    cached += 1
                    check_function(name, body, errors)
                elif any(re.search(r'\br\d+ = ', text) for _, text in body):
                    errors.append(f'{name}: locals without a declaration')
                name = None
                continue
            if DECL.match(line):
                is_cached = True
                continue
            body.append((number, line))
    for error in errors[:60]:
        print(error)
    print(f'{functions} functions, {cached} with cached registers, {len(errors)} violations')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
