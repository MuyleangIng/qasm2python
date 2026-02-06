# qasm2python

Convert OpenQASM 2.0 / 3.0 to executable Python Qiskit code.

Supports:
- OpenQASM 2 and 3
- Standard gates (h, x, cx, ccx, rx, ry, rz, etc.)
- Custom gate definitions
- Automatic modifier sanitization (e.g. `ctrl @`, `ctrl(2) @`)
- Dynamic Python code generation

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

## 🔥 Basic Usage

```python
from qasm2python import convert_qasm_to_python

qasm = """
OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
h q[0];
cx q[0], q[1];
"""

python_code = convert_qasm_to_python(qasm, var_name="qc")
print(python_code)
```

---

## 🧠 Advanced Example (Custom Gate + Modifiers)

Even if your QASM includes modifiers like `ctrl @`, the library will sanitize them automatically.

```python
from qasm2python import convert_qasm_to_python

qasm_custom = """
OPENQASM 3;
include "stdgates.inc";
qubit[5] q;
bit[5] c;

gate kinggate a, b, c, d, e {
  h a;
  h b;
  h a;
  ctrl @ cx b, e;
  ctrl @ cx a, d;
  ctrl(2) @ ccx a, b, c;
  x a;
  rx(1.5708) a;
}

kinggate q[0],q[1],q[2],q[3],q[4];
c[1] = measure q[1];
c[2] = measure q[2];
"""

python_code = convert_qasm_to_python(qasm_custom, var_name="qc")
print(python_code)
```

---

## ▶ Run Generated Circuit

```python
namespace = {}
exec(python_code, namespace)

qc = namespace["qc"]

from qiskit_aer import AerSimulator
from qiskit import transpile

sim = AerSimulator()
tqc = transpile(qc, sim)
result = sim.run(tqc, shots=1024).result()

print(result.get_counts())
```

---

## 🔧 Local Development

Clean previous builds:

```bash
rm -rf dist build *.egg-info
```

Build:

```bash
pip install build
python -m build
```

Install locally:

```bash
pip install dist/qasm2python-0.2.0-py3-none-any.whl
```

---

## 🧩 Features

- QASM2 & QASM3 detection
- Gate conversion to Python Qiskit API
- Custom gate extraction
- Modifier stripping for compatibility
- Ready for Aer simulation

---

## 👤 Author

Muyleang Ing  
AI Convergence Researcher | Quantum Computing | Software & DevOps Engineer  

🌐 https://muyleanging.com  
💻 https://github.com/muyleanging/qasm2python
