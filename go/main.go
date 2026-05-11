package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"time"
)

type ThreatPayload struct {
	AttackerIP string    `json:"attacker_ip"`
	Timestamp  time.Time `json:"timestamp"`
	Payload    string    `json:"payload"`
	TargetPort string    `json:"target_port"`
}

func main() {
	port := "6379" 
	
	listener, err := net.Listen("tcp", "0.0.0.0:"+port)
	if err != nil {
		log.Fatalf("Failed to start trap on port %s: %v", port, err)
	}
	defer listener.Close()

	fmt.Printf("[*] Deception Network Active. Listening for malicious actors on port %s...\n", port)

	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Printf("Failed to accept connection: %v", err)
			continue
		}

		go handleAttacker(conn, port)
	}
}

func handleAttacker(conn net.Conn, port string) {
	defer conn.Close()
	
	// --- NEW FIX: Split the IP from the Port ---
	rawAddress := conn.RemoteAddr().String()
	attackerIP, _, err := net.SplitHostPort(rawAddress)
	if err != nil {
		// Fallback just in case parsing fails
		attackerIP = rawAddress 
	}

	fmt.Printf("[!] Alert: Connection detected from %s\n", attackerIP)

	// Create a buffer to read the attacker's initial injection/command
	buffer := make([]byte, 1024)
	n, err := conn.Read(buffer)
	if err != nil {
		return // Connection dropped before sending data
	}

	// Clean up the payload data
	maliciousData := string(buffer[:n])
	fmt.Printf("[-] Captured Payload: %q\n", maliciousData)

	// Package the telemetry into our struct (now with a clean IP!)
	threat := ThreatPayload{
		AttackerIP: attackerIP,
		Timestamp:  time.Now(),
		Payload:    maliciousData,
		TargetPort: port,
	}

	// Forward the raw data to Phase 3
	forwardToBrain(threat)
}

func forwardToBrain(threat ThreatPayload) {
	jsonData, _ := json.Marshal(threat)

	url := "http://localhost:8000/analyze"
	
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		log.Printf("[!] AI Brain unreachable. Threat logged locally.")
		return
	}
	defer resp.Body.Close()
	
	fmt.Println("[+] Threat data successfully forwarded to the AI Brain for analysis.")
}