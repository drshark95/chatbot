"""Compatibility helpers for loading the project's Gensim 3 Doc2Vec model."""

from pathlib import Path

from gensim import utils
from gensim.models.keyedvectors import KeyedVectors


def _upconvert_old_doc_vectors(keyed_vectors):
    """Convert integer-tagged Gensim 3 Doc2Vec vectors to Gensim 4 fields."""
    if keyed_vectors.max_rawint > -1:
        index_to_key = list(range(keyed_vectors.max_rawint + 1))
        index_to_key.extend(keyed_vectors.offset2doctag)
    else:
        index_to_key = list(keyed_vectors.offset2doctag)

    keyed_vectors.index_to_key = index_to_key
    keyed_vectors.key_to_index = {
        key: index for index, key in enumerate(index_to_key)
    }
    keyed_vectors.expandos = {}
    keyed_vectors.vectors = keyed_vectors.vectors_docs

    for legacy_name in (
        "doctags",
        "vectors_docs",
        "count",
        "max_rawint",
        "offset2doctag",
    ):
        delattr(keyed_vectors, legacy_name)


def load_legacy_doc2vec(model_path):
    """Load the committed Gensim 3 model into the installed Gensim 4 runtime."""
    path = str(Path(model_path))
    original_upconverter = KeyedVectors._upconvert_old_d2vkv
    KeyedVectors._upconvert_old_d2vkv = _upconvert_old_doc_vectors

    try:
        compress, subname = utils.SaveLoad._adapt_by_suffix(path)
        model = utils.unpickle(path)
        if "docvecs" in model.__dict__ and not hasattr(model, "dv"):
            model.dv = model.__dict__.pop("docvecs")
        model._load_specials(path, mmap=None, compress=compress, subname=subname)
        return model
    finally:
        KeyedVectors._upconvert_old_d2vkv = original_upconverter
