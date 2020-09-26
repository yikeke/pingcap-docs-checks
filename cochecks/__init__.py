#!/usr/bin/env python3
# encoding=utf-8

import re
import sys
import os
from optparse import OptionParser

def stack_tag(tag, stack):
    # python implementation of data structure "stack"
    # reference: https://stackoverflow.com/questions/35761133/python-how-to-check-for-open-and-close-tags
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

def check_backticks(content):
    # Check if `` appears in twin
    backticks = []
    open_inline_code = False
    content_findall = re.findall(r'`', content)
    if len(content_findall):
        content_finditer = re.finditer(r'`', content)
        for i in content_finditer:
            pos = list(i.span())
            # which_line is the line number of the matched str
            which_line = content.count('\n', 0, i.start())
            pos.append(which_line)
            backticks.append(pos)
            

        # e.g. backticks = [[23, 24, 3],[37, 38, 4],[123, 124, 7],[147, 148, 9]]
        if len(backticks) % 2 != 0:
            open_inline_code = True
            return open_inline_code, backticks
    return open_inline_code, backticks

def filter_block(content):
    # Remove content wrapped by ` `
    if check_backticks(content):
        open_inline_code, backticks = check_backticks(content)
        if len(backticks) != 0:
            block_start = backticks[0][0]
            block_end = backticks[1][1]
            content = content.replace(content[block_start:block_end],'')
            content = filter_block(content)
    return content

def check_tags(content):
    content = filter_frontmatter(content)
    open_inline_code, backticks = check_backticks(content)
    if open_inline_code:
        stack = False
    else:
        # filter all inline code and code blocks
        content = filter_block(content)
        # print(content)
        stack = []
        result_findall = re.findall(r'<([^\n`>]*)>', content)
        if len(result_findall) != 0:
            result_finditer = re.finditer(r'<([^\n`>]*)>', content)
            for i in result_finditer:
                # print(i.group(), i.span())
                tag = i.group()
                pos = i.span()
                # which_line is the line number of the matched str
                # which_line = content.count('\n', 0, i.start())

                if tag[:4] == '<!--' and tag[-3:] == '-->':
                    continue
                elif content[pos[0]-2:pos[0]] == '{{' and content[pos[1]:pos[1]+2] == '}}':
                    # filter copyable shortcodes
                    continue
                elif tag[:5] == '<http': # or tag[:4] == '<ftp'
                    # filter urls
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
            if not stack:
                print("ERROR: " + tag + ' has open inline code or code blocks, which affects the check for open tags. Please add the missing backtick(s) and run `cocheck` again.\n')
                exit(1)
            elif len(stack):
                stack = ['<' + i + '>' for i in stack]
                print("ERROR: " + tag + ' has unclosed tags: ' + ', '.join(stack) + '.\n')
                # print("HINT: Unclosed tags will cause website build failure. Please fix the reported unclosed tags. You can use backticks `` to wrap them or close them. Thanks.")
                exit(1)

        elif os.path.isdir(tag):
            status_code = 0
            file_with_paths = parse_args_dir(tag)
            for old_file_path in file_with_paths:
                with open(old_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                stack = check_tags(content)
                if not stack:
                    print("ERROR: " + tag + ' has open inline code or code blocks, which affects the check for open tags. Please add the missing backtick(s) and run `cocheck` again.\n')
                elif len(stack):
                    stack = ['<' + i + '>' for i in stack]
                    print("ERROR: " + old_file_path + ' has unclosed tags: ' + ', '.join(stack) + '.\n')
                    status_code = 1
            if status_code:
                # print("HINT: Unclosed tags will cause website build failure. Please fix the reported unclosed tags. You can use backticks `` to wrap them or close them. Thanks.")
                exit(1)
        else:
            print('Please give me a file path or a directory path.')
            exit(1)

    elif block:
        if os.path.isfile(block):
            content = parse_args_file(block)
            open_inline_code, backticks = check_backticks(content)
            if open_inline_code:
                print("ERROR: " + block + ' has unclosed inline code or code blocks in Line' + backticks[-1][-1] + '. Please close them.')
                exit(1)
        elif os.path.isdir(block):
            status_code = 0
            file_with_paths = parse_args_dir(block)
            for old_file_path in file_with_paths:
                with open(old_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                open_inline_code, backticks = check_backticks(content)
                if open_inline_code:
                    print("ERROR: " + old_file_path + ' has unclosed inline code or code blocks in Line ' + str(backticks[-1][-1]) + '. Please close them.')
                    exit(1)
        else:
            print('Please specify a file path or a directory path as the argument.')
    else:
        print('Please specify an option. Execute `cocheck -h` to list all options.')

def exe_main():
    parser = OptionParser(version="%prog 0.0.17")
    parser.set_defaults(verbose=True)
    # parser.add_option("-a", "--all", dest="all",
    #                   help="Checks unclosed tags, code blocks, copyable snippets, etc.", metavar="ALL")
    parser.add_option("-t", "--tag", dest="tag", type="string", 
                      help="Checks unclosed HTML tags and code blocks; Accepts a file path or a directory path as the argument.", metavar="TAG")
    parser.add_option("-b", "--block", dest="block", type="string", 
                      help="Only checks unclosed code blocks; Accepts a file path or a directory path as the argument.", metavar="BLOCK")
    options, args = parser.parse_args()
    process(options)
