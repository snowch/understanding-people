#!/usr/bin/env python3
"""Explicitly embed reading passages using the checked-in local ONNX model.

Requires numpy, tokenizers and onnxruntime (production tooling only). No API/TTS.
Run after a current HTML build; a staging build may skip the vector freshness gate.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from book_search import ASSETS, catalogue, digest, engine, packed
from build import CHAPTERS, PAGES, OUT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rebuild', action='store_true', help='Render current sources before producing vectors')
    args = parser.parse_args()
    if args.rebuild:
        from build import build
        build(include_search=False)
    engine()
    data = catalogue(OUT, PAGES, CHAPTERS)
    tokenizer = Tokenizer.from_file(str(ASSETS / 'models/minilm/tokenizer.json'))
    tokenizer.enable_truncation(max_length=256)
    tokenizer.enable_padding()
    options = ort.SessionOptions(); options.intra_op_num_threads = 2
    session = ort.InferenceSession(str(ASSETS / 'models/minilm/onnx/model_quantized.onnx'), options, providers=['CPUExecutionProvider'])
    rows = []
    for offset in range(0, len(data['passages']), 16):
        batch = data['passages'][offset:offset+16]
        texts = [data['documents'][p['document']]['title'] + '. ' + p['heading'] + '. ' + p['text'] for p in batch]
        enc = tokenizer.encode_batch(texts)
        feed = {'input_ids': np.array([e.ids for e in enc], dtype=np.int64),
                'attention_mask': np.array([e.attention_mask for e in enc], dtype=np.int64),
                'token_type_ids': np.array([e.type_ids for e in enc], dtype=np.int64)}
        output = session.run(None, {i.name: feed[i.name] for i in session.get_inputs()})[0]
        mask = feed['attention_mask'][..., None]
        embeddings = (output*mask).sum(axis=1) / mask.sum(axis=1)
        embeddings /= np.linalg.norm(embeddings, axis=1, keepdims=True)
        quantized = np.rint(embeddings / np.max(np.abs(embeddings), axis=1, keepdims=True) * 127).astype(np.int8)
        rows.append(quantized)
        if offset % 160 == 0:
            print(f'Embedded {offset+len(batch)}/{len(data["passages"])} passages', flush=True)
    vectors = np.concatenate(rows).tobytes()
    (ASSETS / 'vectors.bin').write_bytes(vectors)
    (ASSETS / 'vectors.json').write_text(json.dumps({'version': 1, 'model': 'Xenova/all-MiniLM-L6-v2',
        'corpus_sha256': digest(packed(data)), 'engine_sha256': digest((ASSETS/'engine.json').read_bytes()),
        'passages': len(data['passages']), 'dimensions': 384, 'storage': 'signed-int8-per-row-max127-cosine',
        'vectors_sha256': digest(vectors)}, indent=2)+'\n')
    print(f'Ready: {len(data["documents"])} pages, {len(data["passages"])} passages, {len(vectors):,} bytes of vectors.')


if __name__ == '__main__':
    main()
