# software/vm/Makefile — SPU-13 Sovereign VM build system

CXX ?= c++
CXXFLAGS = -std=c++17 -O2 -Wall
BIN ?= spu_vm

# gen1-surd build identity (SPU-GEN1-SIM-IMPL-0): reported by `spu_vm --profile gen1-surd --capabilities`.
GEN1_INPUTS = Makefile spu_vm.cpp checked_math.h assembly_operands.h gen1_wide.hpp gen1_surd.hpp gen1_cli.hpp
GEN1_SOURCE_SHA256 := $(or $(shell cat $(GEN1_INPUTS) 2>/dev/null | sha256sum 2>/dev/null | cut -c1-64),unknown)
GEN1_REVISION := $(or $(shell r=$$(git rev-parse HEAD 2>/dev/null) && { if [ -n "$$(git status --porcelain -- . 2>/dev/null)" ]; then echo "$$r-dirty"; else echo "$$r"; fi; }),unversioned)
GEN1_BUILD_ID := $(or $(shell printf '%s|%s|%s' '$(GEN1_SOURCE_SHA256)' "$$($(CXX) --version 2>/dev/null | head -n1)" '$(CXXFLAGS)' | sha256sum 2>/dev/null | cut -c1-64),unknown)
GEN1_DEFS = -DGEN1_SOURCE_REVISION='"$(GEN1_REVISION)"' -DGEN1_SOURCE_SHA256='"$(GEN1_SOURCE_SHA256)"' -DGEN1_BUILD_ID='"$(GEN1_BUILD_ID)"'

all: spu_vm

spu_vm: spu_vm.cpp checked_math.h assembly_operands.h gen1_wide.hpp gen1_surd.hpp gen1_cli.hpp
	$(CXX) $(CXXFLAGS) $(GEN1_DEFS) -o $(BIN) spu_vm.cpp

avx2: spu_vm.cpp
	$(CXX) $(CXXFLAGS) -mavx2 -DSPU_AVX2 -o spu_vm_avx2 spu_vm.cpp

wasm: spu_vm.cpp
	emcc -std=c++17 -O2 -o spu_vm.js spu_vm.cpp \
		-s WASM=1 -s EXPORTED_RUNTIME_METHODS='["callMain"]' \
		-s ALLOW_MEMORY_GROWTH=1

clean:
	rm -f spu_vm spu_vm_avx2 spu_vm.js spu_vm.wasm

test: spu_vm
	./spu_vm ../programs/jitterbug.sas --quiet --steps 256; status=$$?; if [ $$status -ne 3 ]; then echo "Expected jitterbug step-budget exit 3, got $$status"; exit 1; fi
	./spu_vm ../programs/equilibrium_test.sas --quiet
	./spu_vm ../programs/pell_octave_test.sas --quiet
	./spu_vm ../programs/isa_test.sas --quiet
	./spu_vm ../programs/quadrance_test.sas --quiet; status=$$?; if [ $$status -ne 2 ]; then echo "Expected quadrance SNAP-failure exit 2, got $$status"; exit 1; fi
	@echo "VM smoke tests passed."

.PHONY: all avx2 wasm clean test
