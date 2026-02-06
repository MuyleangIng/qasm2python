from qiskit import qasm3
from typing import List


def convert_qasm(qasm_source: str) -> str:
    """
    Convert OpenQASM 3 string into Python Qiskit code.
    """
    circuit = qasm3.loads(qasm_source)

    lines: List[str] = []

    n_qubits = circuit.num_qubits
    n_clbits = circuit.num_clbits

    lines.append("from qiskit import QuantumCircuit")
    lines.append(f"qc = QuantumCircuit({n_qubits}, {n_clbits})")
    lines.append("")

    for instruction, qargs, cargs in circuit.data:

        name = instruction.name

        qubits = [circuit.qubits.index(q) for q in qargs]
        clbits = [circuit.clbits.index(c) for c in cargs]

        if name == "h":
            lines.append(f"qc.h({qubits[0]})")

        elif name == "x":
            lines.append(f"qc.x({qubits[0]})")

        elif name == "cx":
            lines.append(f"qc.cx({qubits[0]}, {qubits[1]})")

        elif name == "ccx":
            lines.append(f"qc.ccx({qubits[0]}, {qubits[1]}, {qubits[2]})")

        elif name == "mcx":
            controls = qubits[:-1]
            target = qubits[-1]
            lines.append(f"qc.mcx({controls}, {target})")

        elif name == "measure":
            lines.append(f"qc.measure({qubits[0]}, {clbits[0]})")

        elif name == "barrier":
            lines.append(f"qc.barrier({qubits})")

        else:
            lines.append(f"# Unsupported gate: {name} on {qubits}")

    return "\n".join(lines)
