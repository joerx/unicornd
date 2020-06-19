build: out/unicornd_darwin_amd64 out/unicornd_linux_amd64

out/unicornd_darwin_amd64:
	GOOS=darwin GOARCH=amd64 go build -o out/unicornd_darwin_amd64 .

out/unicornd_linux_amd64:
	GOOS=linux GOARCH=amd64 go build -o out/unicornd_linux_amd64 .

clean:
	rm -rf out

.PHONY: clean build
