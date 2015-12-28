#!/usr/bin/env python3

import os, cgi, cgitb
import time, re, crypt
import html, mistune

markdown = mistune.markdown
cgitb.enable()

# To generate a mod password, use tripcode.py3 to generate a tripkey.
# What comes out is the result of a code that generates something like
# a public key. Type #password in the name field to have your post
# render as the mod_un using a special color. Save your !tripcode in the
# mod_pw field to do so, without an exclamation mark in front. Your tripkey
# should be 10 letters long, the result of an 8 character secure password
# that you know others can't guess easily.
#
# b_url and theme currently are unused.

board_config = \
    [["b_name", "4x13 BBS"], \
     ["b_url", "/bbs/"], \
     ["mod_un", "Admin"], \
     ["mod_pw", "tyF/EWEkIY"], \
     ["theme", "alpha"], \
     ["t_dir", "./threads/"], \
     ["t_list", "./threads/list.txt"], \
     ["t_limit", 100]]

functions = ["main", "thread", "admin", "list", "create", "reply"]
form = cgi.FieldStorage()

def main():
    select_func = form.getvalue('m')
    bbs_header()
    if select_func:
        if select_func in functions:
#            print("<h1>", select_func, "</h1>")
            print("<a href='.'>&lt;&lt; back</a><br>")
            print("----"*10, "<p>")
            if select_func == "admin":
                bbs_admin()
            elif select_func == "main":
                bbs_main()
            elif select_func == "thread":
                bbs_thread()
            elif select_func == "create":
                bbs_create()
            elif select_func == "list":
                bbs_list()
            elif select_func == "reply":
                do_reply()
        else:
            select_func = None
            
    if not select_func:
        bbs_main()

    bbs_foot()

def bbs_header():
    print("Content-type: text/html\n")
    print("<title>{0}</title>".format(board_config[0][1]))
    print("<link rel='stylesheet' href='style.css'>")
    print("<meta name=viewport content='width=850px;initial-scale:device-width'>")
    print("""<script language="javascript">
function addText(elId,text) {
    text = ">>" + text + " \\r";
    document.getElementById(elId).value += text;
}
</script>""")
    
def bbs_admin():
    for confg in board_config:
        print(confg[0]+":", confg[1], "<br>")

def bbs_main():
    print("<h2>{0}</h2>".format(board_config[0][1]))
    with open("motd.txt", "r") as motd:
        motd = motd.read()
        print("<div style='background-color:white; padding-left: 30px; width:580px; border:1px dashed black'>")
        print(markdown(motd))
        print("</div><p>")
    bbs_list()
    print("<p><hr>")
    do_prev()
    print("<hr>")
    bbs_create()

def bbs_thread(t_id='', prev=0):
    if not t_id and form.getvalue('t'):
        t_id = cgi.escape(form.getvalue('t'))
    if t_id:
        if t_id.isdigit():
            t_fn = board_config[5][1] + t_id + ".txt"
        else:
            bbs_list()
            return
    else:
        bbs_list()
        return
    if os.path.isfile(t_fn):
        with open(t_fn, "r") as the_thread:
            the_thread = the_thread.readlines()
            r_cnt = str(len(the_thread) - 1)
            if prev == 0:
                print("<h3>", the_thread[0] + "[" + r_cnt + "]", "</h3>")
                print("<div class='thread'>")
            p_n = 0
            replies=[]
            for reply in the_thread[1:]:
                p_n += 1
                reply = reply.split(' >< ')
                if len(reply) > 4:
                    reply[3] = " >< ".join(reply[3:])
                if reply[2]:
                    reply.pop(2)
                    reply[0] = "<span class='sage'>" \
                        + reply[0] + "</span>"
                else:
                    reply.pop(2) #30c
                    reply[0] = "<span class='bump'>" \
                        + reply[0] + "</span>"
                
                if prev == 0:
                    if re.compile(r'&gt;&gt;[\d]').search(reply[2]):
                        reply[2] = re.sub(r'&gt;&gt;([\d]+)', \
                            r'<a href="#\1">&gt;&gt;\1</a>', reply[2])
                    reply[2] = do_format(reply[2])   
                    print("</p><a name='{0}' href='#reply'".format(p_n))
                    print("onclick='addText(\"{1}\", \"{0}\")'".format(p_n, t_id))
                    print("'>#{0}</a> //".format(p_n))
                    print("Name: {0} :\n Date: {1} \n<p>{2}".format(*reply))
                else:
                    if re.compile(r'&gt;&gt;[\d]').search(reply[2]):
                        reply[2] = re.sub(r'&gt;&gt;([\d]+)', \
                            r'<a href="?m=thread;t={0}#\1">&gt;&gt;\1</a>'.format(t_id), reply[2])
                    reply[2] = do_format(reply[2])
                    if len(reply[2].split('<br>')) > 8:
                        reply[2] = '<br>'.join(reply[2].split('<br>')[:9])[:850] \
                            + "</p><div class='rmr'>Post shortened. " \
                            + "<a href='?m=thread;t={0}'>[".format(t_id) \
                            + "View full thread]</a></div>" 
                    elif len(reply[2]) > 850:
                        reply[2] = reply[2][:850]  + "</p>" \
                            + "<div class='rmr'>Post shortened. " +\
                            "<a href='?m=thread;t={0}'>".format(t_id) \
                            + "[View full thread]</a></div>"
                    elif int(r_cnt) > 4 and p_n == int(r_cnt):
                        reply[2] = reply[2] + "</p><div class='rmr'>" \
                            +"<a href='?m=thread;t={0}'".format(t_id) \
                            +">[Read all posts]</a></div>"
                            
                replies.append(reply)
            if prev == 0:
                print("</div><br>")
                if int(r_cnt) != board_config[7][1]:
                    bbs_reply(t_fn, t_id)
                else:
                    print("<hr>No more replies; thread limit reached!")
            return replies
            
    else:
        bbs_list()
        return
            
def bbs_create():
    thread_attrs = {'title':'', 'name':'', 'content':''}
    for key in thread_attrs.keys():
        if form.getvalue(key):
            thread_attrs[key] = form.getvalue(key)
    if thread_attrs['title'] and thread_attrs['content']:
        thread_attrs['title'] = cgi.escape(thread_attrs['title'])[:25].strip()
        if thread_attrs['name']:
            thread_attrs['name'] = \
                cgi.escape(thread_attrs['name'])[:14].strip()
            if '#' in thread_attrs['name']:
                namentrip = thread_attrs['name'].split('#')[:2]
                namentrip[1] = tripcode(namentrip[1])
                thread_attrs['name'] = '</span> <span class="trip">'.join(namentrip)
        thread_attrs['content'] = cgi.escape(thread_attrs['content']).strip().replace('\r\n', "<br>")[:2000]
        thread_attrs['dt'] = str(time.time())[:10]
        if not thread_attrs['name']:
            thread_attrs['name'] = 'Anonymous'
        local_dt = time.localtime(int(thread_attrs['dt']))
        date_str = "%Y-%m-%d [%a] %H:%M"
        thread_attrs['ldt'] = time.strftime(date_str, local_dt)
        t_fn = board_config[5][1] + thread_attrs['dt'] + ".txt"
        with open(t_fn, "x") as new_thread:
            new_thread.write(thread_attrs['title'] + "\n" \
                + thread_attrs['name'] + " >< " \
                + thread_attrs['ldt'] + " ><  >< " \
                + thread_attrs['content'] + "\n" )
            print("Thread <i>{0}</i> posted successfully!".format(thread_attrs['title']))
            print("<p>Redirecting you in 5 seconds...")
            print("<meta http-equiv='refresh' content='5;.'")
        with open(board_config[6][1]) as t_list:
            t_list = t_list.read().splitlines()
            new_t = " >< ".join([thread_attrs['dt'], \
                thread_attrs['ldt'], thread_attrs['title'], \
                "1"])
            t_list.insert(0, new_t)
        with open(board_config[6][1], "w") as upd_list:
            upd_list.write('\n'.join(t_list))
            
    else:
        if not thread_attrs['title']:
            if thread_attrs['content']:
                print("You need to enter a title to post a new thread.<br>")
        elif not thread_attrs['content']:
            print("You need to write a message to post a new thread.<br>")
        with open("create.html") as c_thread:
            print(c_thread.read())

def bbs_list():
    with open(board_config[6][1]) as t_list:
        t_list = t_list.read().splitlines()
        cnt = 1
        print("<table>")
        print("<th> <th>Title <th>Posts <th>Last post")
        for t in t_list:
            print("<tr><td>{0}.".format(cnt))
            t = t.split(" >< ")
            print("<td><a href='?m=thread;t=" \
            + "{0}'>{2}</a>&nbsp; <td>{3} <td>{1} &nbsp;".format(*t))
            cnt += 1
        print("</table>")

def bbs_reply(t_fn='', t_id=''):
    with open("reply.html") as r_thread:
        print(r_thread.read().format(t_fn, t_id))

def bbs_foot():
    with open("foot.html") as b_foot:
        print(b_foot.read())
        
def do_reply():
    reply_attrs = {'name':'', 'bump':'', 'comment':'', 't':''}
    for key in reply_attrs.keys():
        if form.getvalue(key):
            reply_attrs[key] = form.getvalue(key)
    if reply_attrs['t'] and reply_attrs['comment']:
        reply_attrs['comment'] = cgi.escape(reply_attrs['comment']).strip().replace('\r\n', "<br>").replace("<br><br><br><br>", "<br>")[:5000]
#        reply_attrs['comment']
        if reply_attrs['name']:
            reply_attrs['name'] = \
                cgi.escape(reply_attrs['name'][:14]).strip()
            if '#' in reply_attrs['name']:
                namentrip = reply_attrs['name'].split('#')[:2]
                namentrip[1] = tripcode(namentrip[1])
                if board_config[3][1] in namentrip[1]:
                    namentrip[1] = board_config[2][1]
                    reply_attrs['name'] = '</span> <span class="admin">'.join(namentrip)
                else:
                    reply_attrs['name'] = '</span> <span class="trip">'.join(namentrip)
        else:
            reply_attrs['name'] = "Anonymous"
        if not reply_attrs['bump']:
            reply_attrs['bump'] = "1"
        if reply_attrs['bump'] != "1":
            reply_attrs['bump'] = ''
        local_dt = time.localtime()
        date_str = "%Y-%m-%d [%a] %H:%M"
        reply_attrs['ldt'] = time.strftime(date_str, local_dt)
        reply_string = reply_attrs['name'] + " >< " \
              + reply_attrs['ldt'] + " >< " \
              + reply_attrs['bump'] + " >< " \
              + reply_attrs['comment'] + "\n"
        fale = 0
        with open(reply_attrs['t'], "r") as the_thread:
            ter = the_thread.read().splitlines()
            if (len(ter) - 1) >= board_config[7][1]:
                fale = 1
            else:
                ter = ter[-1].split(' >< ')
                if ter[-1] == reply_string.split(' >< ')[-1][:-1]:
                    fale = 2
                
        with open(reply_attrs['t'], "a") as the_thread:
            if fale == 0:
                the_thread.write(reply_string)
            elif fale == 1:
                print("Sorry, thread limit reached!")
            elif fale == 2:
                print("Sorry, you already posted that.")
        with open(board_config[5][1] + "ips.txt", "a") as log:
            if fale == 0:
                ip = os.environ["REMOTE_ADDR"]
                log_data = " | ".join([ip, reply_attrs['t'], reply_string])
                log.write(log_data)
                print("comment successfully posted<p>")
                print("Redirecting you in 5 seconds...")
                print("<meta http-equiv='refresh' content='5;.'")
            
        with open(board_config[6][1]) as t_list:
            reply_attrs['t'] = ''.join([i for i in reply_attrs['t'] if i.isdigit()])
            t_line = [reply_attrs['t'], reply_attrs['ldt'], reply_attrs['bump']]
            t_list = t_list.read().splitlines()
            nt_list = []
            new_t = []
            for t in t_list:
                t = t.split(' >< ')
                nt_list.append(t)
                if t[0] == t_line[0]:
                    t_line.insert(2, t[2])
                    t_line.insert(3, str(int(t[3])+1))
                    new_t = [' >< '.join(t), ' >< '.join(t_line)]
            sage = 0
            if new_t[1].split(" >< ")[4]:
                new_t[1] = new_t[1][:-4]
                sage = 1
            for n, t in enumerate(nt_list):
                if t[0] == new_t[1].split(" >< ")[0]:
                    if sage == 1:
                        nt_list[n] = new_t[1].split(" >< ")
                        pass
                    else:
                        nt_list.remove(t)
                        nt_list.insert(0, new_t[1].split(" >< "))
                        pass
            for n, l in enumerate(nt_list):
                nt_list[n] = " >< ".join(l)
            with open(board_config[6][1], "w") as new_tl:
                new_tl.write('\n'.join(nt_list))

    else: 
        if not reply_attrs['comment']:
            print("You need to write something to post a comment.")

def do_prev(bbt=[]):
    if not bbt:
        with open(board_config[6][1]) as t_list:
            t_list = t_list.read().splitlines()[:10]
            for t in t_list:
                t = t.split(" >< ")
                bbs = bbs_thread(t[0], 1)
                print("<div class='thread'>")
                do_prev([bbs, t[0]])

    if bbt:
        pstcnt = 0
        bbn = len(bbt[0])
        if bbn > 4:
            bbn = len(bbt[0]) - 2
        else:
            bbn = 1
        with open(board_config[5][1] + str(bbt[1]) + ".txt") as t:
            t_t = t.readline()
            t_r = len(t.read().splitlines())
        print("<h3><a href='?m=thread;t={0}'>{1} [{2}]".format(bbt[1], t_t, len(bbt[0])))
        print("</a></h3>")
        for replies in bbt[0]:
            pstcnt += 1
            if pstcnt == 1 or pstcnt >= bbn:
                print("</p>#{0} //".format(pstcnt))
                print("Name: {0} \n: Date: {1} \n<p>{2}".format(*replies))
            if pstcnt == 1 and len(bbt[0]) > 4:
                print("<hr width='420px' align='left'>")
            elif pstcnt == len(bbt[0]):
                print("</div>")
                if t_r != board_config[7][1]:
                    print("<hr width='420px' align='left'>")
                    bbs_reply(board_config[5][1] + bbt[1]+".txt")
                else:
                    print("<hr>You cannot reply to this thread any longer.<hr>")


def do_format(urp=''):
    urp = re.sub(r'\[yt\]http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?\[/yt\]', r'<iframe width="560" height="315" src="https://www.youtube.com/embed/\1" frameborder="0" allowfullscreen></iframe>', urp) 
    urp = re.sub(r'\[aa\](.*?)\[/aa\]', r'<div class="sjis"><b>SJIS:</b><hr>\1<p></div>', urp)
    urp = re.sub(r'\[spoiler\](.*?)\[/spoiler\]', r'<span class="spoiler">\1</span>', urp)
    urp = re.sub(r'\[code\](.*?)\[/code\]', r'<pre><b>Code:</b><hr><code>\1</code><p></pre>', urp)
    urp = urp.split('<br>')
    for num, line in enumerate(urp):
        if line[:4] == "&gt;":
            urp[num] = "<span class='quote'>"+line+"</span>"
    urp = '<br>'.join(urp)        
    urp = urp.replace('&amp;', '&').encode('ascii', 'xmlcharrefreplace').decode()
    return urp

def tripcode(pw):
    pw = pw[:8]
    salt = (pw + "H..")[1:3]
    trip = crypt.crypt(pw, salt)
    return (" !" + trip[-10:])

main()
        
