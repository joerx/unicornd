package main

import (
	"encoding/json"
	"log"
	"math/rand"
	"net/http"
	"os"
	"time"
)

// UnicornColors is a list of possible colours for Unicorns
// TODO: add support for multi-colored unicorns
// See https://louisem.com/29880/color-thesaurus-infographic
var UnicornColors = []string{
	"cream",
	"alabaster",
	"frost",
	"hazelwood",
	"sepia",
	"oyster",
	"butterscotch",
	"cantaloupe",
	"apricot",
	"amber",
	"watermelon",
	"strawberry",
	"rosewood",
}

// UnicornNames is a name of unicorn names
// Courtesy of https://www.fantasynamegenerators.com/unicorn-names.php
var UnicornNames = []string{
	"Nightwind",
	"Hesperos",
	"Argus",
	"Samantha",
	"Fae",
	"Langaria",
	"Sterling",
	"Snowflake",
	"Starburst",
	"Unity",
}

// UnicornMaxAge is the maximum age a unicorn can have
const UnicornMaxAge = 30

var generator = rand.New(rand.NewSource(time.Now().UnixNano()))

func main() {
	addr, ok := os.LookupEnv("UNICORND_ADDRESS")
	if !ok {
		addr = "localhost:8080" // using localhost avoid the OS firewall promp
	}

	http.HandleFunc("/", handleIndex)
	http.HandleFunc("/unicorn", handleGetUnicorn)
	http.HandleFunc("/health", handleHealth)

	log.Printf("Starting server on %s\n", addr)
	log.Fatal(http.ListenAndServe(addr, nil))
}

type errorResponse struct {
	Error string `json:"error"`
}

type indexRespone struct {
	Message  string `json:"message"`
	Hostname string `json:"hostname"`
}

type healthCheckResponse struct {
	Status string `json:"message"`
}

type unicorn struct {
	Name  string `json:"name"`
	Age   int    `json:"age"`
	Color string `json:"color"`
}

type unicornResponse struct {
	Unicorn *unicorn `json:"unicorn"`
}

func randomElement(lst []string) string {
	idx := generator.Intn(len(lst) - 1)
	return lst[idx]
}

func handleIndex(w http.ResponseWriter, req *http.Request) {
	hostname, _ := os.Hostname()
	resp := &indexRespone{
		Message:  "Hello",
		Hostname: hostname,
	}
	respondOK(w, resp)
}

func handleHealth(w http.ResponseWriter, req *http.Request) {
	resp := &healthCheckResponse{
		Status: "OK",
	}
	respondOK(w, resp)
}

func handleGetUnicorn(w http.ResponseWriter, req *http.Request) {
	unicorn := &unicorn{
		Color: randomElement(UnicornColors),
		Name:  randomElement(UnicornNames),
		Age:   generator.Intn(UnicornMaxAge),
	}
	resp := &unicornResponse{Unicorn: unicorn}
	respondOK(w, resp)
}

func respondOK(w http.ResponseWriter, payload interface{}) {
	bytes, err := json.Marshal(payload)

	if err != nil {
		respondInternalError(w, err)
		return
	}

	w.WriteHeader(http.StatusOK)
	w.Write(bytes)
}

func respondInternalError(w http.ResponseWriter, err error) {
	resp := &errorResponse{
		Error: err.Error(),
	}

	bytes, err := json.Marshal(resp)
	if err != nil {
		log.Fatal(err)
	}

	w.WriteHeader(http.StatusInternalServerError)
	w.Write(bytes)
}
