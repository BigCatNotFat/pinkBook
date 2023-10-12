from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, jsonify
import os
import json
from datetime import datetime
from PIL import Image  # 导入Pillow库中的Image模块

app = Flask(__name__)
DATA_FILE = 'data.json'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
messages = []
message_id = 0
comments = {}
app.secret_key = 'your_secret_key_here'  # 选择一个复杂的字符串作为密钥


def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            # 如果数据不为空，找到当前最大的message_id
            if data:
                max_id = max([msg['id'] for msg in data])
                global message_id
                message_id = max_id + 1
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



@app.route('/', methods=['GET', 'POST'])
def index():

    return render_template('index.html',messages=messages)

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():

    return render_template('addItem.html', messages=messages)

@app.route('/submit_post', methods=['POST'])
def submit_post():
    global message_id
    if request.method == 'POST':
        text = request.form.get('text')
        title = request.form.get('title')
        images = request.files.getlist('images')  # 获取多个文件

        uploaded_image_names = []  # 存储上传的图片文件名的列表
        small_loaded_image_names = []  # 存储上传的图片文件名的列表
        for image in images:
            if image.filename:
                filename = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
                image.save(filename)
                uploaded_image_names.append(image.filename)  # 将文件名添加到列表中

                # 构建缩小后的文件名，添加前缀 "small_"
                small_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'small_' + image.filename)

                # 打开原始文件并缩小图像，然后另存为新的文件名
                with Image.open(filename) as img:
                    img.thumbnail((500, 500))
                    img.save(small_filename)  # 另存为新的文件名
                    small_loaded_image_names.append(small_filename)  # 将新的文件名添加到列表中

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 获取当前时间并格式化
        current_username = session.get('username', 'Anonymous')

        # 在保存到JSON之前，去掉文件路径中的 "uploads\\"
        cleaned_small_image_names = [name.replace(app.config['UPLOAD_FOLDER'] + '\\', '') for name in
                                     small_loaded_image_names]

        messages.append({
            'id': message_id,
            'username': current_username,
            'title': title,
            'text': text,
            'tag': 'all',
            'likes': 0,
            'timestamp': current_time,
            'origin_images': uploaded_image_names,
            'small_images': cleaned_small_image_names  # 使用去掉 "uploads\\" 部分的文件路径

        })

        message_id += 1

        # 保存数据到文件
        save_data(messages)

    return render_template('index.html', messages=messages)

@app.route('/item/<int:item_id>', methods=['GET', 'POST'])
def view_item(item_id):
    item = next((msg for msg in messages if msg['id'] == item_id), None)
    if not item:
        return "Item not found", 404

    # 处理评论提交
    if request.method == 'POST':
        comment_text = request.form.get('comment')
        current_username = session.get('username', 'Anonymous')  # 获取当前用户名，如果未找到则默认为“Anonymous”
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 将用户名拼接到评论前面
        full_comment = {
            'text': f"{current_username}: {comment_text}",
            'timestamp': current_time  # 保存时间戳
        }
        if 'comments' not in item:
            item['comments'] = []
        item['comments'].append(full_comment)

        # 保存更新后的数据到文件
        save_data(messages)

    item_comments = item.get('comments', [])
    return render_template('item.html', messages=item, comments=item_comments)
PER_PAGE = 10  # 每页的帖子数，你可以根据需要调整这个值

@app.route('/posts', methods=['GET'])
def get_posts():
    page = request.args.get('page', 1, type=int)  # 从查询参数中获取页码，默认为1
    start = (page - 1) * PER_PAGE  # 计算起始索引
    end = start + PER_PAGE  # 计算结束索引
    posts = messages[start:end]  # 切片获取相应的帖子
    return jsonify(posts)


messages = load_data()
if __name__ == '__main__':
    app.run(debug=True)
