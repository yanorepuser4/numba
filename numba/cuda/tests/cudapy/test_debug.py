import numpy as np

from numba.core.utils import PYVERSION
from numba.cuda.testing import skip_on_cudasim, CUDATestCase
from numba.tests.support import (override_config, captured_stderr,
                                 captured_stdout)
from numba import cuda, float64
import unittest


def simple_cuda(A, B):
    i = cuda.grid(1)
    B[i] = A[i] + 1.5


@skip_on_cudasim('Simulator does not produce debug dumps')
class TestDebugOutput(CUDATestCase):

    def compile_simple_cuda(self):
        with captured_stderr() as err:
            with captured_stdout() as out:
                cfunc = cuda.jit((float64[:], float64[:]))(simple_cuda)
                # Call compiled function (to ensure PTX is generated)
                # and sanity-check results.
                A = np.linspace(0, 1, 10).astype(np.float64)
                B = np.zeros_like(A)
                cfunc[1, 10](A, B)
                self.assertTrue(np.allclose(A + 1.5, B))
        # stderr shouldn't be affected by debug output
        self.assertFalse(err.getvalue())
        return out.getvalue()

    def assert_fails(self, *args, **kwargs):
        self.assertRaises(AssertionError, *args, **kwargs)

    def check_debug_output(self, out, enabled_dumps):
        all_dumps = dict.fromkeys(['bytecode', 'cfg', 'ir', 'llvm',
                                   'assembly'],
                                  False)
        for name in enabled_dumps:
            assert name in all_dumps
            all_dumps[name] = True
        for name, enabled in sorted(all_dumps.items()):
            check_meth = getattr(self, '_check_dump_%s' % name)
            if enabled:
                check_meth(out)
            else:
                self.assertRaises(AssertionError, check_meth, out)

    def _check_dump_bytecode(self, out):
        if PYVERSION in ((3, 11), (3, 12)):
            # binop with arg=0 is binary add, see CPython dis.py and opcode.py
            self.assertIn('BINARY_OP(arg=0', out)
        elif PYVERSION in ((3, 8), (3, 9), (3, 10)):
            self.assertIn('BINARY_ADD', out)
        else:
            raise NotImplementedError(PYVERSION)

    def _check_dump_cfg(self, out):
        self.assertIn('CFG dominators', out)

    def _check_dump_ir(self, out):
        self.assertIn('--IR DUMP: simple_cuda--', out)
        self.assertIn('const(float, 1.5)', out)

    def _check_dump_llvm(self, out):
        self.assertIn('--LLVM DUMP', out)

    def _check_dump_assembly(self, out):
        self.assertIn('--ASSEMBLY simple_cuda', out)
        self.assertIn('Generated by NVIDIA NVVM Compiler', out)

    def test_dump_bytecode(self):
        with override_config('DUMP_BYTECODE', True):
            out = self.compile_simple_cuda()
        self.check_debug_output(out, ['bytecode'])

    def test_dump_ir(self):
        with override_config('DUMP_IR', True):
            out = self.compile_simple_cuda()
        self.check_debug_output(out, ['ir'])

    def test_dump_cfg(self):
        with override_config('DUMP_CFG', True):
            out = self.compile_simple_cuda()
        self.check_debug_output(out, ['cfg'])

    def test_dump_llvm(self):
        with override_config('DUMP_LLVM', True):
            out = self.compile_simple_cuda()
        self.check_debug_output(out, ['llvm'])

    def test_dump_assembly(self):
        with override_config('DUMP_ASSEMBLY', True):
            out = self.compile_simple_cuda()
        self.check_debug_output(out, ['assembly'])


if __name__ == '__main__':
    unittest.main()
