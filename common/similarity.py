#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Jan 30, 2018
similar.py: data mining for text similarity
@author: Neo
Version: 1.0
'''

import sys, os, logging, multiprocessing, getopt
reload(sys)
sys.setdefaultencoding('utf-8')
#from nltk.stem.porter import PorterStemmer
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

#global variables
english_punctuations = [
    ',', '.', ';', '?', '!', '(', ')', '[', ']', '@', '&', '#', '%', '$', '{',
    '}', '--', '-', "'", ':'
]
model_path = "/home/information/data-mining/model/log.model"
source_path = "/home/information/data-mining/pre_logdata"

# testing sentence
sentence = "reserve setup_data: [mem 0x000000008f889018-0x000000008f8bc057] usable"

# sentence = "efi: mem14: type=2, attr=0xf, range=[0x000000008fa17000-0x000000008fb19000) (1MB)"
# sentence = "pci 0000:07:08.2: [8086:208d] type 00 class 0x088000"
# sentence = "i40e 0000:b0:00.2: irq 41 for MSI/MSI-X"
# sentence = "ata8: SATA link up 6.0 Gbps (SStatus 133 SControl 300)"


# dump in source data
def get_dataset(object):
    global source_path
    srcdata = []
    for root, dirs, files in os.walk(object):
        for f in files:
            file_path = os.path.join(root, f)
            if file_path.find('dmesg') >= 0:
                print "Handle dataset in file: %s..." % file_path
                f = open(file_path, 'r')
                data = f.read().decode('utf8', 'ignore')
                lines = data.split('\n')
                for line in lines:
                    line = line[line.find(']') + 1:] + '\n'
                    srcdata.append(line)
                f.close()
            elif file_path.find('messages') >= 0 and file_path.find(
                    'SUSE') >= 0:
                print "Handle dataset in file: %s..." % file_path
                f = open(file_path, 'r')
                data = f.read().decode('utf8', 'ignore')
                lines = data.split('\n')
                for line in lines:
                    line = line[line.find('linux'):] + '\n'
                    srcdata.append(line)
                f.close()
            elif file_path.find('messages') >= 0 and file_path.find(
                    'RedHat') >= 0:
                print "Handle dataset in file: %s..." % file_path
                f = open(file_path, 'r')
                data = f.read().decode('utf8', 'ignore')
                lines = data.split('\n')
                for line in lines:
                    line = line[line.find('localhost'):] + '\n'
                    srcdata.append(line)
                f.close()
            else:
                pass
    if os.path.exists(source_path):
        os.remove(source_path)
    fw = open(source_path, 'w')
    output = ' '.join(list(srcdata))
    fw.write(output)
    fw.close()
    yield srcdata


# preprocess all the dataset, including tokenize,
# remove stopwords, remove punctuation, and stemming words
def preprocess(dataset):
    global english_puncutations, source_path
    # tokenize
    dataset_tokenized = [[word.lower() for word in word_tokenize(item)]
                         for item in dataset]
    # remove stopwords
    english_stopwords = stopwords.words('english')
    dataset_flr_stopwords = [[
        word for word in item if word not in english_stopwords
    ] for item in dataset_tokenized]
    # remove punctuation
    dataset_flr_punctuation = [[
        word for word in item if word not in english_punctuations
    ] for item in dataset_flr_stopwords]
    # stem words
    # st = PorterStemmer()
    # dataset_stemmed = [[st.stem(word) for word in item] for item in dataset_flr_punctuation]
    # convert data to TaggedDocument
    dataset_processed = dataset_flr_punctuation
    # filename = "/home/information/data-mining/source.txt"
    count = 0
    pre_data = []
    for item in dataset_processed:
        document = TaggedDocument(item, tags=[count])
        pre_data.append(document)
        count += 1
    return pre_data


'''
use doc2vec to train the dataset
class gensim.models.doc2vec.Doc2Vec(documents=None,md_mean=None,dm=1,dbow_words=0,
dm_concat=0,dm_tag_count=1,docvecs=None,docvecs_mapfile=None,trim_rule=None,**kwargs)
dm defines the training algorithm. dm=1 means 'distributed memory' (PV-DM). Otherwise, 'distributed
bag of words' (PV-DBOW) is employed. size is the dimensionality of the feature vectors. window is the maximum
distance between the predicted word and context words used for predicttion within a document.
alpha is the initial learning rate. seed= for random number generator. min_count= ignore all words with total
frequency lower than this. iter= number of iterations over the corpus.hs= if 1, hierarchical softmax will be
used for model training.dm_mean = if 0, use the sum of the content word vector. If 1, use the mean. Only used
when dm is used in non-concatenative mode. dm_concat= if 1, use concatenation of context vectors.
'''


def train(pre_data):
    global model_path
    dm = 0
    cores = multiprocessing.cpu_count()
    size = 50
    context_window = 3
    min_count = 1
    alpha = 0.2
    max_iter = 20
    sample = 1e-1
    negative = 3
    dm_concat = 0
    hs = 1

    model = Doc2Vec(
        dm=dm,
        alpha=alpha,
        min_count=min_count,
        window=context_window,
        size=size,
        sample=sample,
        negative=negative,
        workers=cores,
        hs=hs,
        dm_concat=dm_concat,
        iter=max_iter)
    model.build_vocab(pre_data)
    model.train(pre_data, total_examples=model.corpus_count, epochs=100)
    if os.path.exists(model_path):
        os.remove(model_path)
    model.save(model_path)


def test(sentence):
    global english_punctuation, model_path
    new_model = Doc2Vec.load(model_path)
    sentence = sentence
    # tokenize
    test_tokenized = [word.lower() for word in word_tokenize(sentence)]
    # remove stopwords
    english_stopwords = stopwords.words('english')
    test_stopwords = [
        word for word in test_tokenized if word not in english_stopwords
    ]
    # remove punctuation
    test_punctuation = [
        word for word in test_stopwords if word not in english_punctuations
    ]
    test_text = test_punctuation
    print "===>Testing sentence:\n", ' '.join(list(test_text))
    inferred_vector_dm = new_model.infer_vector(test_text)
    sims = new_model.docvecs.most_similar(positive=[inferred_vector_dm])
    return sims


# print help information
def usage():
    print "usage: {0} [OPTS]".format(os.path.basename(__file__))

    print "  -i, --input <input string>	\
            Input the string you want to compare the similarity"

    print "  -m, --model <input trained model>	\
            input the trained model file you want to use"

    print "  -h, --help		Print this help message"


def main(argv):
    ret = {'input': '', 'model': ''}
    if argv:
        try:
            opts, args = getopt.getopt(argv, "hvi:m:", ["input="])
        except getopt.GetoptError as err:
            print str(err)
            sys.exit(2)
        verbose = False
        for opt, arg in opts:
            if opt == '-v':
                verbose = True
            elif opt in ("-i", "--input"):
                ret['input'] = arg
            elif opt in ("-m", "--model"):
                ret['model'] = arg
            elif opt in ("-h", "--help"):
                usage()
                sys.exit()
            else:
                assert False, "unhandled option"
                print "Verbose value is %s" % (str(verbose))
    return ret


if __name__ == '__main__':
    ret = main(sys.argv[1:])
    logging.basicConfig(
        format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    if ret['model'] == '':
        src_path = "/home/information/log"
        dataset = get_dataset(src_path)
        processed_data = preprocess(dataset.next())
        train(processed_data)
    else:
        model_path = ret['model']
    if ret['input'] != '':
        sentence = ret['input']
        print "Input sentence is: ", sentence
    sims = test(sentence)
    fo = open(source_path, 'r')
    original_data = []
    for line in fo.readlines():
        original_data.append(line)
    fo.close()
    print "The similar sentences are: \n"
    for count, sim in sims:
        if sim > 0.7:
            sentence = original_data[count]
            print "%s, %.2f%%" % (sentence, sim * 100)
