from __future__ import annotations

import re
from typing import Dict, List, Set

from qiskit import QuantumCircuit
from qiskit import qasm2, qasm3
from qiskit.circuit.controlledgate import ControlledGate

# -----------------------------
# Standard gates (not custom)
# -----------------------------
STANDARD_GATES = {
    "id", "i", "x", "y", "z", "h", "s", "sdg", "t", "tdg", "sx", "sxdg",
    "rx", "ry", "rz", "p", "u", "u1", "u2", "u3",
    "cx", "cy", "cz", "swap", "cp",
    "crx", "cry", "crz", "cu",
    "ccx", "cswap", "mcx",
    "rzz",
}


def sanitize_qasm_modifiers(qasm_source: str) -> str:
    """Strip OpenQASM 3 gate modifiers so the code becomes parseable.

    Examples::

        ctrl @ cx b,e;        -> cx b,e;
        ctrl(2) @ ccx a,b,c;  -> ccx a,b,c;
        inv @ x q[0];         -> x q[0];
        pow(3) @ rz(0.1) q[0];-> rz(0.1) q[0];

    This is a SEMANTIC CHANGE. Use only if you intentionally want
    to ignore modifiers.
    """
    out_lines = []
    modifier_re = re.compile(
        r"^\s*(?:ctrl(?:\(\s*\d+\s*\))?|negctrl(?:\(\s*\d+\s*\))?|"
        r"inv|pow\(\s*[-+]?\d+\s*\))\s*@\s*"
    )
    for line in qasm_source.splitlines():
        s = line.strip()

        # Keep empty/comment lines unchanged
        if not s or s.startswith("//"):
            out_lines.append(line)
            continue

        if "@" in s:
            s2 = s
            while True:
                new = modifier_re.sub("", s2)
                if new == s2:
                    break
                s2 = new
            out_lines.append(s2)
        else:
            out_lines.append(line)

    return "\n".join(out_lines)


def load_any_qasm(qasm_source: str) -> QuantumCircuit:
    """Load an OpenQASM 2 or 3 source string and return a QuantumCircuit.

    Attempts to auto-detect the QASM version from the header. Falls back
    to heuristic detection when the first line is not a version directive.

    Parameters:
        qasm_source: The OpenQASM source code.

    Returns:
        A Qiskit ``QuantumCircuit`` parsed from the source.

    Raises:
        ValueError: If the OPENQASM version cannot be detected.
    """
    header = qasm_source.strip().splitlines()[0].strip()

    # QASM3
    if header.startswith("OPENQASM 3"):
        try:
            return qasm3.loads(qasm_source)
        except Exception:
            cleaned = sanitize_qasm_modifiers(qasm_source)
            return qasm3.loads(cleaned)

    # QASM2
    if header.startswith("OPENQASM 2"):
        return qasm2.loads(qasm_source)

    # Heuristic fallback
    if "OPENQASM 3" in qasm_source:
        try:
            return qasm3.loads(qasm_source)
        except Exception:
            cleaned = sanitize_qasm_modifiers(qasm_source)
            return qasm3.loads(cleaned)

    if "OPENQASM 2" in qasm_source:
        return qasm2.loads(qasm_source)

    raise ValueError("Cannot detect OPENQASM version.")


# -----------------------------
# Utilities
# -----------------------------


def _fmt_param(x) -> str:
    """Format a gate parameter as a Python repr string."""
    return repr(x)


def _qindex(circ: QuantumCircuit, q) -> int:
    """Return the integer index of qubit *q* within *circ*."""
    return circ.qubits.index(q)


def _cindex(circ: QuantumCircuit, c) -> int:
    """Return the integer index of classical bit *c* within *circ*."""
    return circ.clbits.index(c)


# -----------------------------
# Main converter
# -----------------------------


def convert_qasm_to_python(
    qasm_source: str,
    var_name: str | None = None,
    include_imports: bool = True,
) -> str:
    """Convert OpenQASM 2/3 to Python Qiskit code.

    Parameters:
        qasm_source: QASM input string.
        var_name: Name of generated ``QuantumCircuit`` variable
            (default: ``"qc"``).
        include_imports: Whether to include import statements.

    Returns:
        Generated Python code as a single string.
    """
    if var_name is None:
        var_name = "qc"

    circuit = load_any_qasm(qasm_source)
    lines: List[str] = []

    if include_imports:
        lines.append("from qiskit import QuantumCircuit")
        lines.append("")

    # -----------------------------
    # Collect custom gate definitions
    # -----------------------------
    custom_defs: Dict[str, QuantumCircuit] = {}

    def collect(inst):
        """Recursively collect custom (non-standard) gate definitions."""
        name = getattr(inst, "name", "")
        definition = getattr(inst, "definition", None)

        if definition and name not in STANDARD_GATES:
            if name not in custom_defs:
                custom_defs[name] = definition
                for sub_inst, _, _ in definition.data:
                    collect(sub_inst)

    for inst, _, _ in circuit.data:
        collect(inst)

    # -----------------------------
    # Emit custom gate builders
    # -----------------------------
    emitted: Set[str] = set()

    def emit_gate(name: str, def_circ: QuantumCircuit):
        """Emit a helper function that builds a custom gate."""
        if name in emitted:
            return
        emitted.add(name)

        lines.append(f"def build_{name}():")
        lines.append(
            f"    g = QuantumCircuit("
            f"{def_circ.num_qubits}, name={name!r})"
        )

        for sub_inst, qargs, cargs in def_circ.data:
            qs = [def_circ.qubits.index(q) for q in qargs]
            cs = (
                [def_circ.clbits.index(c) for c in cargs]
                if def_circ.num_clbits
                else []
            )
            _emit_instruction(
                lines, "g", sub_inst, qs, cs, indent="    "
            )

        lines.append("    return g.to_gate()")
        lines.append("")

    for name, def_circ in custom_defs.items():
        emit_gate(name, def_circ)

    # -----------------------------
    # Emit main circuit
    # -----------------------------
    lines.append(
        f"{var_name} = QuantumCircuit("
        f"{circuit.num_qubits}, {circuit.num_clbits})"
    )
    lines.append("")

    for inst, qargs, cargs in circuit.data:
        qs = [_qindex(circuit, q) for q in qargs]
        cs = [_cindex(circuit, c) for c in cargs]
        _emit_instruction(lines, var_name, inst, qs, cs)

    return "\n".join(lines)


# -----------------------------
# Instruction emitter
# -----------------------------


def _emit_instruction(
    lines: List[str],
    circ_var: str,
    inst,
    qs: List[int],
    cs: List[int],
    indent: str = "",
) -> None:
    """Emit a single Qiskit instruction as a line of Python code.

    Parameters:
        lines: Accumulator list to which generated code lines are appended.
        circ_var: Name of the circuit variable in the generated code.
        inst: A Qiskit instruction / gate object.
        qs: Integer indices of the qubits involved.
        cs: Integer indices of the classical bits involved.
        indent: Leading whitespace for the emitted line.
    """
    name = inst.name
    params = getattr(inst, "params", []) or []
    p = [_fmt_param(x) for x in params]

    # --------------------------------
    # ctrl(...) @ gate (QASM 3)
    # --------------------------------
    if isinstance(inst, ControlledGate):
        controls = qs[:-1]
        target = qs[-1]
        k = inst.num_ctrl_qubits
        base = inst.base_gate.name

        if base == "x" and k == 1:
            lines.append(
                f"{indent}{circ_var}.cx({controls[0]}, {target})"
            )
            return

        if base == "x" and k == 2:
            lines.append(
                f"{indent}{circ_var}.ccx("
                f"{controls[0]}, {controls[1]}, {target})"
            )
            return

        lines.append(
            f"{indent}{circ_var}.mcx({controls}, {target})"
        )
        return

    # --------------------------------
    # Measurement / barrier / reset
    # --------------------------------
    if name == "measure":
        lines.append(
            f"{indent}{circ_var}.measure({qs[0]}, {cs[0]})"
        )
        return

    if name == "barrier":
        lines.append(f"{indent}{circ_var}.barrier({qs})")
        return

    if name == "reset":
        lines.append(f"{indent}{circ_var}.reset({qs[0]})")
        return

    # --------------------------------
    # Single-qubit gates
    # --------------------------------
    if name in {"id", "i"}:
        lines.append(f"{indent}{circ_var}.id({qs[0]})")
        return

    if name in {
        "x", "y", "z", "h", "s", "sdg", "t", "tdg", "sx", "sxdg",
    }:
        lines.append(f"{indent}{circ_var}.{name}({qs[0]})")
        return

    if name in {"rx", "ry", "rz", "p"}:
        lines.append(
            f"{indent}{circ_var}.{name}({p[0]}, {qs[0]})"
        )
        return

    if name == "u":
        lines.append(
            f"{indent}{circ_var}.u("
            f"{p[0]}, {p[1]}, {p[2]}, {qs[0]})"
        )
        return

    # --------------------------------
    # Two-qubit gates
    # --------------------------------
    if name in {"cx", "cy", "cz", "swap"}:
        lines.append(
            f"{indent}{circ_var}.{name}({qs[0]}, {qs[1]})"
        )
        return

    if name == "cp":
        lines.append(
            f"{indent}{circ_var}.cp({p[0]}, {qs[0]}, {qs[1]})"
        )
        return

    if name in {"crx", "cry", "crz"}:
        lines.append(
            f"{indent}{circ_var}.{name}("
            f"{p[0]}, {qs[0]}, {qs[1]})"
        )
        return

    # --------------------------------
    # Three+ qubit
    # --------------------------------
    if name == "ccx":
        lines.append(
            f"{indent}{circ_var}.ccx("
            f"{qs[0]}, {qs[1]}, {qs[2]})"
        )
        return

    if name == "mcx":
        lines.append(
            f"{indent}{circ_var}.mcx({qs[:-1]}, {qs[-1]})"
        )
        return

    # --------------------------------
    # Custom gate call
    # --------------------------------
    if (
        getattr(inst, "definition", None) is not None
        and name not in STANDARD_GATES
    ):
        lines.append(
            f"{indent}{circ_var}.append(build_{name}(), {qs})"
        )
        return

    # --------------------------------
    # Fallback
    # --------------------------------
    lines.append(
        f"{indent}# Unsupported gate: {name} "
        f"params={p} qubits={qs}"
    )
