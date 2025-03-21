#!/usr/bin/env python3
##############################################################
import asyncio
import glob
import os

import pytesseract
from pdf2image import convert_from_path
import multiprocessing

import trio
import trio_parallel


class TrioQueue:
    queue = set()

    def put(self, item):
        self.queue.add(item)

    async def get(self):
        while True:
            if self.queue.__len__():
                return self.queue.pop()
            await trio.sleep(0.1)


class State:
    # files = TrioQueue()
    def __init__(self, proc_limit: int = 4):
        self.limit = proc_limit
        self.running = 0



async def parallel_map(fn, inputs, *args):
    results = [None] * len(inputs)

    async def worker(j, inp):
        s.running += 1
        ret = await trio_parallel.run_sync(fn, inp, *args)
        if ret:
            results[j] = ret
        s.running -= 1
        print(j, "done")


    async with trio.open_nursery() as nursery:
        for i, inp in enumerate(inputs):
            while True:
                if s.running < s.limit:
                    nursery.start_soon(worker, i, inp)
                    break
                else:
                    await trio.sleep(0.01)
    return results


def save_text(output, text):
    with open(output, 'w') as f:
        f.write(text)


def ocr_pdf_to_text(file: str):
    ff = file.split("/")[1]
    fname = f'text/{ff}.txt'
    # print(f'[+] Processing {x + 1}/{len(files)} : ' + ff)
    if os.path.exists(fname):
        return None
    images = convert_from_path(file)  # Convert PDF pages to images
    text_output = ""

    for i, img in enumerate(images):
        text = pytesseract.image_to_string(img)  # Apply OCR
        text_output += f"\n--- Page {i + 1} ---\n{text}\n"

    save_text(fname, text_output)
    return text_output


def split_into_chunks(file_list: list[str], n: int) -> list[list[str]]:
    """
    Splits a list of files into smaller lists of size n.

    :param file_list: List of file names.
    :param n: Size of each chunk.
    :return: A list of smaller lists, each containing up to n file names.
    """
    return [file_list[i:i + n] for i in range(0, len(file_list), n)]


async def amain(_files):
    chunks = split_into_chunks(_files, s.limit)
    for chunk in chunks:
        ret = await parallel_map(ocr_pdf_to_text, chunk)
        print(ret)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    s = State(4)
    files = glob.glob('files/*')
    if not len(files):
        print('[!] Please download the pdf files first')
        exit(1)
    print('[~] NOTICE: This program is fairly resource intensive. Please allocate at least 16 gigs of RAM and 8 cpu '
          'cores in order to avoid performance bottleneck issues.')
    print(trio.run(amain, files))

