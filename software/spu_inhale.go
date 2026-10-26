package main

/*
 * spu_inhale.go (v1.1 - Sovereign Manifold Monitor)
 * Objective: Read 104-byte Whisper frames from the SPU-13.
 * Standard: Q12 Rational Field Visualization.
 *
 * Usage:
 *   go run spu_inhale.go                        # real hardware via /dev/ttyACM0
 *   go run spu_inhale.go --port /dev/ttyUSB0    # specify port
 *   go run spu_inhale.go --emulate              # software emulator, no hardware needed
 */

import (
	"flag"
	"fmt"
	"io"
	"log"
	"math"
	"time"

	"github.com/tarm/serial"
)

const (
	axes       = 13
	frameBytes = axes * 8 // 104
	q12        = 4096.0
)

// Fibonacci-derived phase offsets matching rp2040_emulator.c
var axisPhase = [axes]float64{
	0.0, 27.7, 55.4, 83.1, 110.8, 138.5, 166.2,
	193.8, 221.5, 249.2, 276.9, 304.6, 332.3,
}

var axisAmp = [axes]float64{
	1.0, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70,
	0.65, 0.60, 0.55, 0.50, 0.45, 0.40,
}

func displayFrame(buf []byte) {
	fmt.Printf("\033[H\033[2J")
	fmt.Println("━━━ Sovereign Manifold State (Q12 Rational Field) ━━━━━━━━━━━━━━")
	fmt.Println("Axis │ Rational (a)  │ Surd (b·√3)   │ Davis C (a/b)  │ Laminar")
	fmt.Println("─────┼───────────────┼───────────────┼────────────────┼────────")

	sumABCD := 0.0
	for i := 0; i < axes; i++ {
		offset := i * 8
		// Big-endian int16, Q12 fixed-point
		aRaw := int16(uint16(buf[offset])<<8 | uint16(buf[offset+1]))
		bRaw := int16(uint16(buf[offset+4])<<8 | uint16(buf[offset+5]))

		a := float64(aRaw) / q12
		b := float64(bRaw) / q12

		// Davis C = a/b (manifold tension ratio); show ∞ when b≈0
		davisC := "    ∞   "
		if math.Abs(b) > 0.001 {
			davisC = fmt.Sprintf("%+7.3f ", a/b)
		}

		// Laminar status: stable if |a²  - 3b²| < 0.01 (Q(√3) quadrance check)
		quadrance := a*a - 3*b*b
		laminar := "✓"
		if math.Abs(quadrance) > 0.1 {
			laminar = "⚠"
		}

		sumABCD += a + b
		fmt.Printf(" %02d  │ %+10.4f    │ %+10.4f    │ %s│  %s\n",
			i, a, b, davisC, laminar)
	}

	// Davis Law global check: ΣABCD should be 0 (no cubic leak)
	fmt.Println("─────┴───────────────┴───────────────┴────────────────┴────────")
	leakStatus := "✓ LAMINAR"
	if math.Abs(sumABCD) > 0.1 {
		leakStatus = "⚠ CUBIC LEAK DETECTED"
	}
	fmt.Printf("ΣABCD = %+.4f   Davis Law: %s\n", sumABCD, leakStatus)
}

// emulateLoop generates Jitterbug frames in software — no hardware needed.
func emulateLoop() {
	fmt.Println("⚙️  Software emulator mode — no hardware required")
	fmt.Println("   Generating Jitterbug manifold animation at 20 Hz...")
	time.Sleep(500 * time.Millisecond)

	t := 0.0
	buf := make([]byte, frameBytes)

	for {
		for i := 0; i < axes; i++ {
			phase := t + axisPhase[i]*(math.Pi/180.0)
			amp := axisAmp[i]

			a := int16(math.Cos(phase) * q12 * amp)
			b := int16(math.Sin(phase) * q12 * amp / math.Sqrt(3))

			offset := i * 8
			buf[offset+0] = byte(a >> 8)
			buf[offset+1] = byte(a)
			buf[offset+4] = byte(b >> 8)
			buf[offset+5] = byte(b)
		}

		displayFrame(buf)

		t += 0.08
		if t > 2*math.Pi {
			t -= 2 * math.Pi
		}
		time.Sleep(50 * time.Millisecond)
	}
}

func main() {
	emulate := flag.Bool("emulate", false, "Software emulator mode (no hardware needed)")
	port := flag.String("port", "/dev/ttyACM0", "Serial port for RP2040 connection")
	flag.Parse()

	fmt.Println("🛰️  SPU-13 Artery Link: Online. Inhaling Manifold...")

	if *emulate {
		emulateLoop()
		return
	}

	c := &serial.Config{Name: *port, Baud: 921600}
	s, err := serial.OpenPort(c)
	if err != nil {
		log.Fatalf("Cannot open %s: %v\nTip: use --emulate to run without hardware", *port, err)
	}

	buf := make([]byte, frameBytes)
	for {
		// io.ReadFull guarantees all 104 bytes before proceeding
		_, err := io.ReadFull(s, buf)
		if err != nil {
			log.Fatal(err)
		}
		displayFrame(buf)
	}
}
