# software/vm/Makefile — SPU-13 Sovereign VM build system

CXX ?= c++
CXXFLAGS = -std=c++17 -O2 -Wall

all: spu_vm

spu_vm: spu_vm.cpp
	$(CXX) $(CXXFLAGS) -o spu_vm spu_vm.cpp

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
