# IMPORTS
import math
import string
import requests
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from newsapi import NewsApiClient
import os
from dotenv import load_dotenv


while True:
    # INPUT
    image_url = input("Enter an image link you want to check for plagiarism: ")
    print("Loading...")


    # FUNCTIONS
    def get_words_from_line_list(text):
        translation_table = str.maketrans(string.punctuation + string.ascii_uppercase, " " * len(string.punctuation) + string.ascii_lowercase)
        text = text.translate(translation_table)
        word_list = text.split()
        return word_list

    def count_frequency(word_list):
        d = {}
        for new_word in word_list:
            if new_word in d:
                d[new_word] = d[new_word] + 1
            else:
                d[new_word] = 1
        return d

    def word_frequencies_for_file(text):
        line_list = text
        word_list = get_words_from_line_list(line_list)
        freq_mapping = count_frequency(word_list)
        return freq_mapping

    def dot_product(d1, d2):
        sum = 0.0
        for key in d1:
            if key in d2:
                sum += (d1[key] * d2[key])
        return sum

    def vector_angle(d1, d2):
        numerator = dot_product(d1, d2)
        denominator = math.sqrt(dot_product(d1, d1) * dot_product(d2, d2))
        return math.acos(numerator / denominator)

    def text_similarity(text1, text2):
        distance = vector_angle(word_frequencies_for_file(text1), word_frequencies_for_file(text2))
        return distance


    # API CALLS
    load_dotenv()

    optiic_api_url = "https://api.optiic.dev/process"
    optiic_api_key = os.getenv("OPTIIC_API_KEY")
    data = {"mode": "ocr", "url": image_url, "apiKey": optiic_api_key}
    response = requests.get(optiic_api_url, params=data)
    try:
        data = response.json()["text"]
        if data == "":
            print("Hmm.. No text detected. Try again with an image with text. Example: https://i.imgur.com/7z2V2xw.jpeg\n")
            continue
        print(f"Your text is:\n{data}\n")
        data = data.replace("\n", " ")
    except KeyError:
        print("Hmm.. That doesn't look like a valid image link. Example: https://i.imgur.com/7z2V2xw.jpeg\n")
        continue
    except:
        print("Hmm.. Looks like you've run out of Optiic API requests. Make a new API key and try again.\n")
        break

    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(data)
    filtered_sentence = [w for w in word_tokens if not w.lower() in stop_words and w.isalpha()]

    query = ""
    for i in filtered_sentence:
        if len(query) + len(i) <= 95:
            if filtered_sentence.index(i) == 0:
                query += i
            else:
                query += " AND " + i

    news_api_key = os.getenv("NEWS_API_KEY")
    news_api = NewsApiClient(api_key=news_api_key)
    response = news_api.get_everything(q=query,
                                      sources='bbc-news,cnn,the-washington-post',
                                      language='en',
                                      sort_by='relevancy',
                                      page_size=5)

    articles = response.get("articles")
    text_similarity_dict = {}
    count = 0
    for i in articles:
        url = requests.get(i.get("url"))
        soup = BeautifulSoup(url.text, 'html.parser')
        percentage = (1-text_similarity(data, soup.get_text().replace("\n", " "))/(math.pi/2))*100
        if percentage > 15:
            text_similarity_dict[count] = {"title": i.get("title"), "url": i.get("url"), "source": i.get("source").get("name"), "percentage": "{0:.2f}".format(percentage)}
            count += 1


    # OUTPUT
    if not text_similarity_dict:
        print("No plagiarism issues found. Looks like your text is unique!")
    else:
        print("Your text may be plagiarised. Please check the below article(s) and edit/remove the plagiarised parts.")
        for i in range(len(text_similarity_dict)):
            print(f"{text_similarity_dict[i]['title']} | {text_similarity_dict[i]['source']} | {text_similarity_dict[i]['url']} | {text_similarity_dict[i]['percentage']}% plagiarised")
    break
