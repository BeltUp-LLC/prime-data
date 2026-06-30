#!/usr/bin/env python3
"""
split_dataset.py — split a primes_1T.bin into 1 GB chunks + SHA-256 manifest

USAGE
-----
  python split_dataset.py primes_1T.bin
  python split_dataset.py primes_1T.bin --chunk-gb 4   # 4 GB chunks instead

OUTPUT
------
  primes_1T_part001.bin
  primes_1T_part002.bin
  ...
  primes_1T.sha256    (SHA-256 checksum per chunk, verify with sha256sum -c)
"""

import sys
import os
import argparse
import hashlib


def split(src: str, chunk_bytes: int):
    base = os.path.splitext(src)[0]
    manifest = base + '.sha256'
    part = 1
    written = 0

    with open(src, 'rb') as f_in, open(manifest, 'w') as f_sha:
        out_path = f'{base}_part{part:03d}.bin'
        f_out = open(out_path, 'wb')
        sha = hashlib.sha256()
        chunk_written = 0
        total_size = os.path.getsize(src)
        print(f'Source : {src}  ({total_size / 1e9:.1f} GB)')
        print(f'Chunks : {chunk_bytes // (1 << 30)} GB each')
        print()

        buf_size = 1 << 22  # 4 MB read buffer
        while True:
            buf = f_in.read(buf_size)
            if not buf:
                break

            remaining = chunk_bytes - chunk_written
            if len(buf) <= remaining:
                f_out.write(buf)
                sha.update(buf)
                chunk_written += len(buf)
                written += len(buf)
            else:
                # split the buffer across two chunks
                first = buf[:remaining]
                rest  = buf[remaining:]

                f_out.write(first)
                sha.update(first)
                f_out.close()
                digest = sha.hexdigest()
                f_sha.write(f'{digest}  {os.path.basename(out_path)}\n')
                print(f'  wrote {out_path}  {digest[:12]}...')

                part += 1
                out_path = f'{base}_part{part:03d}.bin'
                f_out = open(out_path, 'wb')
                sha = hashlib.sha256()
                chunk_written = 0

                f_out.write(rest)
                sha.update(rest)
                chunk_written = len(rest)
                written += len(buf)

            pct = written / total_size * 100
            print(f'\r  {written / 1e9:.2f} / {total_size / 1e9:.1f} GB  ({pct:.1f}%)   ',
                  end='', flush=True)

        # close last chunk
        if chunk_written > 0:
            f_out.close()
            digest = sha.hexdigest()
            f_sha.write(f'{digest}  {os.path.basename(out_path)}\n')
            print(f'\n  wrote {out_path}  {digest[:12]}...')

    print()
    print(f'Done.  {part} chunks.  Manifest: {manifest}')
    print(f'Verify with: sha256sum -c {manifest}')


def main():
    parser = argparse.ArgumentParser(
        description='Split a primes_1T.bin into chunks with SHA-256 manifest.')
    parser.add_argument('file', help='Source .bin file')
    parser.add_argument('--chunk-gb', type=int, default=1,
                        metavar='N', help='Chunk size in GB (default 1)')
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f'Error: {args.file} not found', file=sys.stderr)
        sys.exit(1)

    split(args.file, args.chunk_gb * (1 << 30))


if __name__ == '__main__':
    main()
