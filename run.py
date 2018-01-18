
# coding: utf-8

# In[7]:

import pandas as pd
import codecs


# In[23]:

# open file for analysis
filename = "./data/app_review_bugs_test.csv"
file = codecs.open(filename,"r","utf8")
dt = pd.read_csv(file)
file.close()


# In[9]:

# cut out useless fields and rows with ratings less than 4 
dt_4 = dt[dt['Rating'] < 4]
dt_4_p = dt_4.drop(['Device', "Device Type", "Date", "AppName", "Language", "Index"], axis=1)


# In[10]:

# removing punctuation marks to '.' and conversation to lower case
before_lemm = list(dt_4_p.Review)
separates = u".,!?;:()[]{}\n"
separates_for_remove = u'"\'$@#%^&*+-=\|/№'
for i in range(len(before_lemm)):
    before_lemm[i] = unicode(str(before_lemm[i]), 'utf8')
    for j in separates_for_remove:
        before_lemm[i] = before_lemm[i].replace(j, u" ")
    for j in separates:
        before_lemm[i] = before_lemm[i].replace(j, u" . ")

    before_lemm[i] = before_lemm[i].replace(u" но ", u" . ")
    before_lemm[i] = before_lemm[i].replace(u" а ", u" . ")
    before_lemm[i] = before_lemm[i].replace(u".  что ", u" . ")
    
    before_lemm[i] = before_lemm[i].lower()


# In[24]:

# open file for lemmatization
# w[0] - form
# w[1] - lemma

# you need to open archive new_dict.rar for this file
dict_file_name = "utils/new_dict.txt"
file_lemm = open(dict_file_name, "r")
lemm_str = file_lemm.readlines()

lemm_arr_form = []
lemm_arr_orig = []
for string in lemm_str:
    string=unicode(str(string), 'utf8')
    string=string.replace("\n", "")
    w = string.split(" ")
    lemm_arr_form.append(w[0])
    lemm_arr_orig.append(w[1])

dict_file_name.close()


# In[12]:

# just binary searching
def bin_search(arr, word):
   l=0
   r=len(arr)
   while(r-l > 1):
      m = (r + l) // 2
      if word < arr[m]:
         r=m
      else:
         l=m
   return l if arr[l]==word else -1

def correct_text(text, lemm_arr_form, lemm_arr_orig):
    new = []
    reviews = len(text)
    for i in range(reviews):
        if type(text[i]) != unicode:
            review1 = unicode(str(text[i]), 'utf8')
        else:
            review1 = unicode(text[i])
        words = review1.split(u" ")
        new_words = u""
        for w in words:
            index = bin_search(lemm_arr_form, w)
            if index != -1:
                w=lemm_arr_orig[index]
            new_words += w + u" "
        new.append(new_words)
    return new


# In[13]:

# getting lemms for words in text
after_lemmatisation = correct_text(before_lemm, lemm_arr_form, lemm_arr_orig)


# In[14]:

# reading noisy words 
filename_noise = "./utils/noise_words.csv"
file_noise = codecs.open(filename_noise,"r","utf8")
noise_words = pd.read_csv(file_noise, sep=" ", names=['idx', 'Freq', 'Word', 'Type'])
noise_words = noise_words.drop(['idx', 'Freq', 'Type'], axis=1)
file_noise.close()


# In[15]:

# removing noisy words
n_first_noise_words = 10000
first = noise_words.Word[0:n_first_noise_words]
first_list = list(first)

#to unicode
for i in range(len(first_list)):
    if type(first_list[i]) != unicode:
        first_list[i] = unicode(str(first_list[i]), 'utf8')
first_list.sort()

after_noise = []
indexes = []

removed = 0
not_removed = 0
for i in range(len(after_lemmatisation)):
    words = after_lemmatisation[i].split(u" ")
    new_text = u""
    local_indexes = []
    for j in range(len(words)):
        w = words[j]
        if w.find(u".")>-1 or w == u"":
            continue
        index = bin_search(first_list, w)
        if index == -1:
            new_text += w + u" "
            local_indexes.append(j)
            not_removed +=1
        else:
            removed +=1
    after_noise.append(new_text)
    indexes.append(local_indexes)

print "were words = " + str(removed + not_removed)
print "removed = " + str(removed)


# In[16]:

# reading key words
key_words_file = "./utils/key_words.csv"
file_key = codecs.open(key_words_file,"r","utf8")
key_words_df = pd.read_csv(file_key, sep=",")
key_words=list(key_words_df["word"])
scores=list(key_words_df["score"])
file_key.close()


# In[19]:

# do key words searching
size = len(after_lemmatisation)
points_for_word = 10
results = []

# loop by reviews
for i in range(size):
    lemm = after_lemmatisation[i].split(u" ")
    source = before_lemm[i].split(u" ")
    
    # do score calculation for each word
    n_words=len(lemm)
    scores_for_words=[]
    for j in range(n_words):
        scores_for_words.append(0)
        if j in indexes[i]:
            scores_for_words[j] += points_for_word
        if lemm[j] in key_words:
            idx = key_words.index(lemm[j])
            scores_for_words[j] += scores[idx]
    prev=0
    sentence = []
    
    # compute score for each sentence
    for j in range(n_words):
        if lemm[j] == ".":
            score = 0
            for k in range(prev,j):
                score += scores_for_words[k]
            sentence.append([score, prev, j])           
            prev = j
    if prev < n_words -1:
        score = 0
        for k in range(prev,n_words):
            score += scores_for_words[k]
        sentence.append([score, prev, n_words])
    
    # choose 1 sentense with max score
    max = 0
    idx = 0
    for j in range(len(sentence)):
        if sentence[j][0] > max:
            max = sentence[j][0]
            idx = j
    if len(sentence) == 0:
        continue
    x = sentence[idx][1]
    if x !=0:
        x +=1
    y = sentence[idx][2]
    results.append(" ".join(source[x:y]).encode("utf-8"))


# In[20]:

# removing useless spases 
for i in range(len(results)):
    if len(results[i])>0:
        while(results[i][0] == " "):
            results[i] = results[i][1:]
            if len(results[i]) == 0:
                break
    if len(results[i])>0:
        while(results[i][len(results[i])-1] == " "):
            results[i] = results[i][0:len(results[i])-1]
            if len(results[i]) == 0:
                break
    while results[i].find("  ")>-1:
        results[i] = results[i].replace("  ", " ")


# In[21]:

# examples of result
for i in range(20):
    print results[i]


# In[22]:

#to file
out_file_name = "results.txt"
file = open(out_file_name, "w+")

res = dt.copy()

ratings = list(res["Rating"])
reviews = list(res["Review"])

file.write("Review,IsBag,KeyWords\n")


size = len(ratings)
idx = 0
for i in range(size):
    string = str(reviews[i]) + ","
    if ratings[i]>=4:
        string += "false,"
    else:
        string += "true," + results[idx]
        idx+=1
    file.write(string + "\n")
file.close()


# In[ ]:



