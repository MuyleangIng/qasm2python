# qasm2python

Convert OpenQASM 2.0 / 3.0 into executable Python Qiskit code.

Supports:
- OpenQASM 2 and 3
- Standard gates (h, x, cx, ccx, rx, ry, rz, etc.)
- Custom gate definitions
- Modifier sanitization (`ctrl @`, `ctrl(2) @`)
- Optional variable naming

---

## 🚀 Installation

```bash
pip install qasm2python
```

Upgrade:

```bash
pip install --upgrade qasm2python
```

---

## 🔥 Basic Usage (Default Variable Name)

If you do not specify `var_name`, it defaults to `qc`.

```python
from qasm2python import convert_qasm_to_python

qasm = """
OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
h q[0];
cx q[0], q[1];
"""

python_code = convert_qasm_to_python(qasm)
print(python_code)
```

Output:

```python
from qiskit import QuantumCircuit

qc = QuantumCircuit(2, 0)
qc.h(0)
qc.cx(0, 1)
```

---

## 🧠 Custom Variable Name (Optional)

You can override the default circuit variable:

```python
python_code = convert_qasm_to_python(qasm, var_name="my_circuit")
print(python_code)
```

Output:

```python
my_circuit = QuantumCircuit(2, 0)
```

---

## 🧪 Execute Generated Circuit

```python
namespace = {}
exec(python_code, namespace)

qc = namespace["qc"]  # or namespace["my_circuit"]
```

---

## 🧠 Advanced Example (Custom Gate + Modifier Sanitization)

Even if QASM includes modifiers like `ctrl @`, they are automatically sanitized.

```python
qasm_custom = """
OPENQASM 3;
include "stdgates.inc";
qubit[5] q;
bit[5] c;

gate kinggate a, b, c, d, e {
  h a;
  ctrl @ cx b, e;
  ctrl(2) @ ccx a, b, c;
}

kinggate q[0],q[1],q[2],q[3],q[4];
"""

python_code = convert_qasm_to_python(qasm_custom)
print(python_code)
```

---

## ⚙ Function Signature

```python
convert_qasm_to_python(
    qasm_source: str,
    var_name: str | None = None,
    include_imports: bool = True
)
```

### Parameters

| Parameter | Description |
|------------|-------------|
| `qasm_source` | QASM 2.0 or 3.0 input string |
| `var_name` | Optional QuantumCircuit variable name (default: `"qc"`) |
| `include_imports` | Whether to include `from qiskit import QuantumCircuit` |

---

## 👤 Author

Muyleang Ing  
AI Convergence Researcher | Quantum Computing | Software & DevOps Engineer  

🌐 https://muyleanging.com  
💻 https://github.com/muyleanging/qasm2python
