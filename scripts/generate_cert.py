"""
Generiert ein selbstsigniertes Zertifikat (cert.pem + key.pem) mit
subjectAltName im aktuellen Arbeitsverzeichnis.

Ausfuehrung:
    cd <app-verzeichnis>
    venv\Scripts\python.exe scripts\generate_cert.py

Oder mit explizitem Serial:
    venv\Scripts\python.exe scripts\generate_cert.py 1001
"""
import os
import sys
from OpenSSL import crypto


def main(serial: int = 1000) -> None:
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)

    cert = crypto.X509()
    cert.get_subject().C = 'CH'
    cert.get_subject().O = 'Achermann & Co. AG'
    cert.get_subject().CN = '192.168.1.202'
    cert.set_serial_number(serial)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365 * 24 * 60 * 60 * 3)  # 3 Jahre
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)

    san = b'IP:192.168.1.202, DNS:localhost, IP:127.0.0.1'
    cert.add_extensions([
        crypto.X509Extension(b'subjectAltName', False, san),
        crypto.X509Extension(b'basicConstraints', True, b'CA:FALSE'),
    ])

    cert.sign(k, 'sha256')

    cwd = os.getcwd()
    cert_path = os.path.join(cwd, 'cert.pem')
    key_path = os.path.join(cwd, 'key.pem')

    with open(cert_path, 'wb') as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    with open(key_path, 'wb') as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

    print(f'Zertifikat mit SAN erstellt in: {cwd}')
    print(f'  cert.pem  ({os.path.getsize(cert_path)} bytes)')
    print(f'  key.pem   ({os.path.getsize(key_path)} bytes)')
    print(f'  Serial:   {serial}')
    print(f'  SAN:      {san.decode()}')
    print(f'  Gueltig:  3 Jahre')


if __name__ == '__main__':
    serial = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    main(serial)
