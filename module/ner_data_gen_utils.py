def tokenize_and_preserve_labels(tokens_lst, labels_lst):
    tokenized_sentence = []
    labels = []
    for word, label in zip(tokens_lst, labels_lst):
        tokenized_word = tokenizer.tokenize(word)
        n_subwords = len(tokenized_word)

        tokenized_sentence.extend(tokenized_word)

        if label[-1] == 'B' and n_subwords > 1:
            tail = list(label)
            tail[-1] = 'I'
            tail = ''.join(tail)
            labels.extend([label] + [tail]*(n_subwords-1))
        else:
            labels.extend([label] * n_subwords)

    return tokenized_sentence, labels