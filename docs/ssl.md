## SSL
This is made possible by creating a self-signed key. First make sure you have
the newest **patched** version of openssl.
Then generate a private key file:
```bash
$ openssl genrsa > key.pem
```
Then generate a self-signed SSL certificate:
```bash
$ openssl req -new -x509 -key key.pem -out cacert.pem -days 1000
```

Finally you can run single SSL server by running:
```bash
$ hx start --dev --key key.pem --cert cacert.pem
```
or a process distributed set of SSL servers:
```bash
hx start --dev --key key.pem --cert cacert.pem -w 3
```
Just go to `https://[insert hostname]:4430/` to check it out.
N.B. Your browser will warn you not to trust the site... You can also specify
which port you want to use by passing the desired number to the `--https_port`
option
