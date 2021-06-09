from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views import generic

from .models import Question, Choice

from .ThreatHound import *
import sys
import os
import argparse
import requests
import re
import json
import threading
import traceback
from multiprocessing import Pool, Process
from datetime import datetime
from OTXv2 import OTXv2
from OTXv2 import IndicatorTypes
from color import cprint, cprint_cyan, cprint_yellow, cprint_red, FgColor


# Create your views here.

feed_ids = []
cache_mode = False

def index(request):

    logo = print_banner()

    args = arg_parse()

    threat_feeds_db = get_threat_feeds_db()

    if args['feed_id']:
        cache_mode = True

    if args['ip']:
        target_ip = args['ip']

    elif args['domain']:
        target_domain = args['domain']

    elif args['ipfile']: 
        inputFile = args['ipfile']

    if args['output']:
        save_file_flag = True
        output_file = args['output']

    if args['local']:
        local_mode = True
        online_mode = False
        cache_mode = False

    elif args['online']:
        online_mode = True         
        local_mode = False
        cache_mode = False

    else:
        cache_mode = True
        local_mode = False
        online_mode = False

    if args['db']:
        REPUTATION_DB_PATH = args['db']
        if not os.path.isdir(REPUTATION_DB_PATH):
            os.mkdir(REPUTATION_DB_PATH)

    # cache模式,先下载feed情报数据
    # if cache_mode:
        #  
        # cacheModeThread(cache_mode, args)
            

    # 离线查询模式直接进行情报搜索
    # if local_mode:
    #     try:
    #         if 'target_ip' in locals():
    #             target_list = [target_ip]
    #         elif 'target_domain' in locals():
    #             target_list = [target_domain]
    #         else:
    #             target_list = parse_input_file(inputFile)
            
    #         # 针对目标进行低信誉ip检索
    #         search_from_feeds(target_list)
    #         # detecting_threat_from_feeds(target_list)
    #         print_flaged_item()
    #         if 'save_file_flag' in locals():
    #             save_file(detect_results, output_file)
    #     except:
    #         cprint_red("Error")
    #         traceback.print_exc()


    
    if 'all' in args['feed_id']:
            feed_ids = [ f['feed_id'] for f in threat_feeds_db ]
            # for f_id in feed_ids:
            #     resultArray.append(get_feeds(f_id))

    else:
        if len(args['feed_id']) == 1:
            start_id = int(args['feed_id'][0])
            stop_id = start_id + 1
        elif len(args['feed_id']) == 2:
            start_id = int(args['feed_id'][0])
            stop_id = int(args['feed_id'][1]) + 1 
        else:
            cprint_red('Invaild feed id!')
            sys.exit(1)

        # for f_id in range(start_id, stop_id, 1):
            # resultArray.append(get_feeds(f_id))

    print('-----from-----')
    print(cache_mode)
    print('------here----')
    context = {
        'logo': logo,
        'feed_ids': feed_ids,
        'threat_feeds_db': threat_feeds_db,
        'cache_mode': cache_mode
    }

    return render(request, 'polls/index.html', context)

def ajaxForRerender(request):
    print('----- start -----')
    print(cache_mode)
    print('---------------end------------')
    idx = request.POST.get('index', None)
    question = cacheModeThread (True, arg_parse(), idx)

    return JsonResponse({"ajaxForRerender": question}, status = 200)
    # else :    
        # return JsonResponse({"error": "ErrorData"}, status = 400)
    # return JsonResponse({"error": ""}, status = 400)

def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'polls/detail.html', {'question': question})

def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'polls/results.html', {'question': question})

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))