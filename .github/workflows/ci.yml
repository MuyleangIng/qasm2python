# tests/test_converter.py
# Place this at: tests/test_converter.py in your qasm2python repo
# Run with: pytest tests/ -v

import pytest
from qasm2python import convert_qasm_to_python


# ── Basic conversion ──────────────────────────────────────

def test_simple_bell_circuit():
    qasm = """
OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
h q[0];
cx q[0], q[1];
"""
    result = convert_qasm_to_python(qasm)
    assert "QuantumCircuit" in result
    assert "qc.h(0)" in result
    assert "qc.cx(0, 1)" in result


def test_default_variable_name_is_qc():
    qasm = "OPENQASM 3;\nqubit[1] q;\nh q[0];"
    result = convert_qasm_to_python(qasm)
    assert "qc = QuantumCircuit" in result


def test_custom_variable_name():
    qasm = "OPENQASM 3;\nqubit[1] q;\nh q[0];"
    result = convert_qasm_to_python(qasm, var_name="my_circuit")
    assert "my_circuit = QuantumCircuit" in result
    assert "qc" not in result.split("=")[0]  # default name not used


def test_include_imports_true():
    qasm = "OPENQASM 3;\nqubit[1] q;\nh q[0];"
    result = convert_qasm_to_python(qasm, include_imports=True)
    assert "from qiskit import QuantumCircuit" in result


def test_include_imports_false():
    qasm = "OPENQASM 3;\nqubit[1] q;\nh q[0];"
    result = convert_qasm_to_python(qasm, include_imports=False)
    assert "from qiskit import QuantumCircuit" not in result


# ── Gate coverage ─────────────────────────────────────────

def test_single_qubit_gates():
    qasm = """
OPENQASM 3;
include "stdgates.inc";
qubit[1] q;
x q[0];
y q[0];
z q[0];
s q[0];
t q[0];
"""
    result = convert_qasm_to_python(qasm)
    for gate in ["qc.x(0)", "qc.y(0)", "qc.z(0)", "qc.s(0)", "qc.t(0)"]:
        assert gate in result, f"Missing gate: {gate}"


def test_rotation_gates():
    qasm = """
OPENQASM 3;
include "stdgates.inc";
qubit[1] q;
rx(1.5707) q[0];
ry(3.1415) q[0];
rz(0.7854) q[0];
"""
    result = convert_qasm_to_python(qasm)
    assert "qc.rx(" in result
    assert "qc.ry(" in result
    assert "qc.rz(" in result


def test_ccx_toffoli():
    qasm = """
OPENQASM 3;
include "stdgates.inc";
qubit[3] q;
ccx q[0], q[1], q[2];
"""
    result = convert_qasm_to_python(qasm)
    assert "qc.ccx(0, 1, 2)" in result


# ── Modifier sanitization ─────────────────────────────────

def test_ctrl_modifier_sanitized():
    """ctrl @ and ctrl(2) @ modifiers should not crash the converter."""
    qasm = """
OPENQASM 3;
include "stdgates.inc";
qubit[3] q;
gate mygate a, b, c {
  ctrl @ cx a, b;
  ctrl(2) @ ccx a, b, c;
}
mygate q[0], q[1], q[2];
"""
    result = convert_qasm_to_python(qasm)
    assert "QuantumCircuit" in result   # should still produce valid output


# ── Output is executable Python ───────────────────────────

def test_output_is_executable():
    """The generated code should actually run via exec()."""
    qasm = """
OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
h q[0];
cx q[0], q[1];
"""
    try:
        from qiskit import QuantumCircuit  # skip if qiskit not installed
    except ImportError:
        pytest.skip("qiskit not installed")

    code = convert_qasm_to_python(qasm)
    namespace = {}
    exec(code, namespace)
    assert "qc" in namespace
    circuit = namespace["qc"]
    assert circuit.num_qubits == 2


# ── Edge cases ────────────────────────────────────────────

def test_empty_qasm_does_not_crash():
    result = convert_qasm_to_python("OPENQASM 3;")
    assert isinstance(result, str)


def test_openqasm2_syntax():
    qasm = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0], q[1];
"""
    result = convert_qasm_to_python(qasm)
    assert "QuantumCircuit" in result
