
# qasm2python

Convert OpenQASM 3 to Python Qiskit code.

## Install

```bash
pip install qasm2python
````

## Usage

```python
from qasm2python import convert_qasm

qasm = """
OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
h q[0];
cx q[0], q[1];
"""

print(convert_qasm(qasm))
```



---

# 🔧 STEP 6 — Install Locally (Test Before Upload)

Inside project folder:

```

pip install build
python -m build

```

Then:

```

pip install dist/qasm2python-0.1.0-py3-none-any.whl

````

Test:

```python
from qasm2python import convert_qasm
````