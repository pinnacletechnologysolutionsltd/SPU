CXX      ?= g++
CXXFLAGS ?= -std=c++17 -Wall -O2 -I../../common/include
TARGET   := davis_monitor

.PHONY: all clean

all: $(TARGET)

$(TARGET): main.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

clean:
	rm -f $(TARGET)
