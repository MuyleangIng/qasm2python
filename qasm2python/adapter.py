from __future__ import annotations

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


import re

def convert_qasm_to_python(qasm_source: str, var_name: str = None, include_imports: bool = True):
    """
    Convert an OpenQASM 2.0 or 3.0 string into executable Qiskit Python code.

    Args:
        qasm_source (str): The QASM source code to convert.
        var_name (str, optional): Name for the QuantumCircuit variable. Defaults to 'qc'.
        include_imports (bool): Whether to include the qiskit import line. Defaults to True.

    Returns:
        str: A string of Python code that creates a Qiskit QuantumCircuit.

    Example:
        >>> code = convert_qasm_to_python("OPENQASM 3; qubit[1] q; h q[0];")
        >>> print(code)
    """

def sanitize_qasm_modifiers(qasm_source: str) -> str:
    """
    Strip OpenQASM 3 gate modifiers so the code becomes parseable.
    Examples:
      ctrl @ cx b,e;        -> cx b,e;
      ctrl(2) @ ccx a,b,c;  -> ccx a,b,c;
      inv @ x q[0];         -> x q[0];
      pow(3) @ rz(0.1) q[0];-> rz(0.1) q[0];

    This is a SEMANTIC CHANGE. Use only if you intentionally want to ignore modifiers.
    """
    out_lines = []
    for line in qasm_source.splitlines():
        s = line.strip()

        # Keep empty/comment lines unchanged
        if not s or s.startswith("//"):
            out_lines.append(line)
            continue

        # Strip repeated modifiers like: ctrl, ctrl(2), inv, negctrl, pow(...)
        # Pattern: <modifier> @ <modifier> @ ... <gatecall>
        # We'll remove everything up to the last '@'
        # Example: "ctrl @ cx a, b;" -> "cx a, b;"
        if "@" in s:
            # Remove sequences like: "ctrl @", "ctrl(2) @", "inv @", "negctrl @", "pow(2) @"
            # repeatedly, until no modifier remains.
            s2 = s
            while True:
                new = re.sub(
                    r"^\s*(?:ctrl(?:\(\s*\d+\s*\))?|negctrl(?:\(\s*\d+\s*\))?|inv|pow\(\s*[-+]?\d+\s*\))\s*@\s*",
                    "",
                    s2,
                )
                if new == s2:
                    break
                s2 = new

            # Preserve original indentation by replacing the stripped content only
            # (simple: just output stripped line without leading spaces)
            out_lines.append(s2)
        else:
            out_lines.append(line)

    return "\n".join(out_lines)


# -----------------------------
# Load QASM2 or QASM3
# -----------------------------

def load_any_qasm(qasm_source: str):
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
    return repr(x)


def _qindex(circ: QuantumCircuit, q) -> int:
    return circ.qubits.index(q)


def _cindex(circ: QuantumCircuit, c) -> int:
    return circ.clbits.index(c)


# -----------------------------
# Main converter
# -----------------------------
def convert_qasm_to_python(
    qasm_source: str,
    var_name: str | None = None,
    include_imports: bool = True,
) -> str:
    """
    Convert OpenQASM 2/3 to Python Qiskit code.

    Parameters:
        qasm_source (str): QASM input string
        var_name (str, optional): Name of generated QuantumCircuit variable (default: "qc")
        include_imports (bool): Whether to include import statements

    Returns:
        str: Generated Python code
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
        if name in emitted:
            return
        emitted.add(name)

        lines.append(f"def build_{name}():")
        lines.append(f"    g = QuantumCircuit({def_circ.num_qubits}, name={name!r})")

        for inst, qargs, cargs in def_circ.data:
            qs = [def_circ.qubits.index(q) for q in qargs]
            cs = [def_circ.clbits.index(c) for c in cargs] if def_circ.num_clbits else []
            _emit_instruction(
                lines, "g", inst, qs, cs, indent="    "
            )

        lines.append("    return g.to_gate()")
        lines.append("")

    for name, def_circ in custom_defs.items():
        emit_gate(name, def_circ)

    # -----------------------------
    # Emit main circuit
    # -----------------------------
    lines.append(f"{var_name} = QuantumCircuit({circuit.num_qubits}, {circuit.num_clbits})")
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
):
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
            lines.append(f"{indent}{circ_var}.cx({controls[0]}, {target})")
            return

        if base == "x" and k == 2:
            lines.append(f"{indent}{circ_var}.ccx({controls[0]}, {controls[1]}, {target})")
            return

        lines.append(f"{indent}{circ_var}.mcx({controls}, {target})")
        return

    # --------------------------------
    # Measurement / barrier
    # --------------------------------
    if name == "measure":
        lines.append(f"{indent}{circ_var}.measure({qs[0]}, {cs[0]})")
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

    if name in {"x", "y", "z", "h", "s", "sdg", "t", "tdg", "sx", "sxdg"}:
        lines.append(f"{indent}{circ_var}.{name}({qs[0]})")
        return

    if name in {"rx", "ry", "rz", "p"}:
        lines.append(f"{indent}{circ_var}.{name}({p[0]}, {qs[0]})")
        return

    if name == "u":
        lines.append(f"{indent}{circ_var}.u({p[0]}, {p[1]}, {p[2]}, {qs[0]})")
        return

    # --------------------------------
    # Two-qubit gates
    # --------------------------------
    if name in {"cx", "cy", "cz", "swap"}:
        lines.append(f"{indent}{circ_var}.{name}({qs[0]}, {qs[1]})")
        return

    if name == "cp":
        lines.append(f"{indent}{circ_var}.cp({p[0]}, {qs[0]}, {qs[1]})")
        return

    if name in {"crx", "cry", "crz"}:
        lines.append(f"{indent}{circ_var}.{name}({p[0]}, {qs[0]}, {qs[1]})")
        return

    # --------------------------------
    # Three+ qubit
    # --------------------------------
    if name == "ccx":
        lines.append(f"{indent}{circ_var}.ccx({qs[0]}, {qs[1]}, {qs[2]})")
        return

    if name == "mcx":
        lines.append(f"{indent}{circ_var}.mcx({qs[:-1]}, {qs[-1]})")
        return

    # --------------------------------
    # Custom gate call
    # --------------------------------
    if getattr(inst, "definition", None) is not None and name not in STANDARD_GATES:
        lines.append(f"{indent}{circ_var}.append(build_{name}(), {qs})")
        return

    # --------------------------------
    # Fallback
    # --------------------------------
    lines.append(f"{indent}# Unsupported gate: {name} params={p} qubits={qs}")
