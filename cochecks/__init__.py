#!/usr/bin/env python3
# encoding=utf-8

import re
import sys
import os
from optparse import OptionParser

# reference: https://stackoverflow.com/questions/35761133/python-how-to-check-for-open-and-close-tags
def stack_tag(tag, stack):
    # python implementation of data structure "stack"
    t = tag[1:-1]
    first_space = t.find(' ')
    #print(t)
    if t[-1:] == '/':
        self_closed_tag = True
    elif t[:1] != '/':
        # Add tag to stack
        if first_space == -1:
            stack.append(t)
            # print("TRACE open", stack)
        else:
            stack.append(t[:first_space])
            # print("TRACE open", stack)
    else:
        if first_space != -1:
            t = t[1:first_space]
        else:
            t = t[1:]

        if len(stack) == 0:
            # print("No blocks are open; tried to close", t)
            closed_tag = True
        else:
            if stack[-1] == t:
                # Close the block
                stack.pop()
                # print("TRACE close", t, stack)
            else:
                # print("Tried to close", t, "but most recent open block is", stack[-1])
                if t in stack:
                    stack.remove(t)
                    # print("Prior block closed; continuing")

    # if len(stack):
    #     print("Blocks still open at EOF:", stack)
    return stack

def tag_is_wrapped(pos, content):
    tag_start = pos[0]
    tag_end = pos[1]
    content_previous = content[:tag_start][::-1] # reverse content_previous
    content_later = content[tag_end:]

    left_wraps_findall = re.findall(r'`', content_previous)
    left_single_backtick = len(left_wraps_findall) % 2
    right_wraps_findall = re.findall(r'`', content_later)
    right_single_backtick = len(right_wraps_findall) % 2
    # print(left_single_backtick, right_single_backtick)

    if left_single_backtick != 0 and right_single_backtick != 0:
        # print(content_previous.find('`'), content_later.find('`'))
        # print(content_previous)
        # print(content_later)
        return True
    else:
        return False

def filter_frontmatter(content):
    # if there is frontmatter, remove it
    if content.startswith('---'):
        collect = []
        content_finditer = re.finditer(r'---\n', content)
        for i in content_finditer:
            meta_pos = i.span()[1]
            collect.append(meta_pos)

        filter_point = collect[1]
        content = content[filter_point:]
    return content

def check_block(content):
    # Check if all code blocks are wrapped with ```
    # And remove content wrapped by backticks
    backticks = []
    content_findall = re.findall(r'```', content)
    unclosed_blocks = 0
    if len(content_findall):
        content_finditer = re.finditer(r'```', content)
        for i in content_finditer:
            pos = i.span()
            backticks.append(pos)
        # e.g. backticks = [[23, 26],[37, 40],[123, 126],[147, 150]]
        if len(backticks) % 2 != 0:
            # print(len(content_findall))
            # print(backticks)
            # print(backticks[0][0], backticks[0][1])
            # print(content[backticks[0][0]-10:backticks[0][1]+10])
            unclosed_blocks = 1
        elif len(backticks) != 0:
            backticks_start = backticks[0][0]
            backticks_end = backticks[1][1]
            content = content.replace(content[backticks_start:backticks_end],'')
            unclosed_blocks, content = check_block(content)

    return unclosed_blocks, content

def check_tags(content):
    content = filter_frontmatter(content)
    unclosed_blocks, content = check_block(content)

    # print(content)
    stack = []
    result_findall = re.findall(r'<([^\n`>]*)>', content)
    if len(result_findall) != 0:
        result_finditer = re.finditer(r'<([^\n`>]*)>', content)
        for i in result_finditer:
            # print(i.group(), i.span())
            tag = i.group()
            pos = i.span()

            if tag[:4] == '<!--' and tag[-3:] == '-->':
                continue
            elif content[pos[0]-2:pos[0]] == '{{' and content[pos[1]:pos[1]+2] == '}}':
                # filter copyable shortcodes
                continue
            elif tag[:5] == '<http': # or tag[:4] == '<ftp'
                # filter urls
                continue
            elif tag_is_wrapped(pos, content):
                # print(content[int(pos[0])-1:int(pos[1]+1)])
                # print(tag, 'is wrapped by backticks!')
                continue

            stack = stack_tag(tag, stack)

    return stack

def parse_args_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def parse_args_dir(path):
    file_with_paths = []
    for root, dirs, files in os.walk(path, topdown=True):
        for name in files:
            full_path = os.path.join(root, name)
            file_with_paths.append(full_path)
    return file_with_paths

def process(opt):
    tag, block = opt.tag, opt.block
    if tag:
        if os.path.isfile(tag):
            content = parse_args_file(tag)
            stack = check_tags(content)
            if len(stack):
                stack = ['<' + i + '>' for i in stack]
                print("ERROR: " + path + ' has unclosed tags: ' + ', '.join(stack) + '.\n')
                # print("HINT: Unclosed tags will cause website build failure. Please fix the reported unclosed tags. You can use backticks `` to wrap them or close them. Thanks.")
                exit(1)

        elif os.path.isdir(tag):
            status_code = 0
            file_with_paths = parse_args_dir(tag)
            for old_file_path in file_with_paths:
                with open(old_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                stack = check_tags(content)
                if len(stack):
                    stack = ['<' + i + '>' for i in stack]
                    print("ERROR: " + old_file_path + ' has unclosed tags: ' + ', '.join(stack) + '.\n')
                    status_code = 1

            if status_code:
                # print("HINT: Unclosed tags will cause website build failure. Please fix the reported unclosed tags. You can use backticks `` to wrap them or close them. Thanks.")
                exit(1)

        else:
            print('Please give me a file path or a directory path.')

    elif block:
        if os.path.isfile(block):
            content = parse_args_file(block)
            unclosed_blocks, content = check_block(content)
            if unclosed_blocks:
                print("ERROR: " + path + ' has unclosed code blocks. Please close them.')
                exit(1)

        elif os.path.isdir(block):
            status_code = 0
            file_with_paths = parse_args_dir(tag)
            for old_file_path in file_with_paths:
                with open(old_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                unclosed_blocks, content = check_block(content)
                if unclosed_blocks:
                    print("ERROR: " + old_file_path + ' has unclosed code blocks. Please close them.')
                    status_code = 1

            if status_code:
                exit(1)

        else:
            print('Please specify a file path or a directory path as the argument.')

    else:
        print('Please specify an option. Execute `cocheck -h` to list all options.')
        # print(parser.print_help())

def exe_main():
    parser = OptionParser(version="%prog 0.0.14")
    parser.set_defaults(verbose=True)
    # parser.add_option("-a", "--all", dest="all",
    #                   help="Checks unclosed tags, code blocks, copyable snippets, etc.", metavar="ALL")
    parser.add_option("-t", "--tag", dest="tag", type="string", 
                      help="Checks unclosed HTML tags and code blocks; Accepts a file path or a directory path as the argument.", metavar="TAG")
    parser.add_option("-b", "--block", dest="block", type="string", 
                      help="Only checks unclosed code blocks; Accepts a file path or a directory path as the argument.", metavar="BLOCK")
    # parser.add_option("-s", "--snippet", dest="snippet", type="string", 
    #                   help="Checks unclosed copyable snippets", metavar="SNIPPET")

    options, args = parser.parse_args()
    process(options)