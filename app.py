"""
Zero Touch App — Indian Social Media Platform
================================================
A full-featured desi social network combining the best of Reddit,
Instagram, Pinterest & YouTube — made for Bharat.

Routes:
  Auth      → /login  /register  /logout
  Gram      → /         (Feed)
  Tez       → /tez      (Trending)
  Saaj      → /saaj     (Boards)
  Reel      → /reel     (Shorts/Videos)
  Samaj     → /samaj    (Communities)
  Pehchaan  → /profile/<username>
"""

import os
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, abort
)
from models import (
    db, User, Post, Community, Board, Pin,
    Like, Comment, Notification, followers_table
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'zerotouch-bharat-2024-desi-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zerotouch_social.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


# ─── Auth Helpers ────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Pehle login karo! 🔐', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

app.jinja_env.globals['current_user'] = current_user


# ─── Seed Data ───────────────────────────────────────────────────

def seed_data():
    if User.query.first():
        return

    # Seed users
    users_data = [
        {'phone': '9876543210', 'username': 'RahulDilli', 'bio': 'Dilli ka banda 🏙️ | Cricket 🏏 | Street Food 🥘', 'seed': 'RahulDilli'},
        {'phone': '9123456780', 'username': 'PriyaMumbai', 'bio': 'Filmon ki deewani 🎬 | Bollywood fan | Mumbai 🏙️', 'seed': 'PriyaMumbai'},
        {'phone': '9000011111', 'username': 'AmarBengaluru', 'bio': 'Software engineer 💻 | Startup ecosystem | Filter coffee ☕', 'seed': 'AmarBengaluru'},
    ]
    users = []
    for ud in users_data:
        u = User(phone=ud['phone'], username=ud['username'], bio=ud['bio'], avatar_seed=ud['seed'], karma=random_karma())
        u.set_password('password123')
        db.session.add(u)
        users.append(u)
    db.session.flush()

    # Seed communities
    communities_data = [
        {'name': 'Cricket', 'emoji': '🏏', 'desc': 'IPL, Tests, T20 — sab kuch cricket!'},
        {'name': 'Bollywood', 'emoji': '🎬', 'desc': 'Latest films, songs, gossip!'},
        {'name': 'StreetFood', 'emoji': '🥘', 'desc': 'Gali gali mein swaad hai'},
        {'name': 'TechStartup', 'emoji': '🚀', 'desc': 'Made in India innovation'},
        {'name': 'DesiMemes', 'emoji': '😂', 'desc': 'Teri wali bhasha mein memes'},
        {'name': 'Yoga', 'emoji': '🧘', 'desc': 'Aastha aur swasthya'},
    ]
    communities = []
    for cd in communities_data:
        c = Community(name=cd['name'], description=cd['desc'], emoji=cd['emoji'], creator_id=users[0].id)
        db.session.add(c)
        communities.append(c)
    db.session.flush()

    # Make users join communities
    for u in users:
        for c in communities[:3]:
            c.members.append(u)

    # Seed posts
    posts_data = [
        {'content': 'Aaj IPL match ka mazaa hi kuch alag tha! MI ne phir se jeet darj ki! 🏏🔥 Kya aap ne dekha? #Cricket #IPL #MumbaiIndians', 'tags': '#Cricket #IPL', 'user': users[0], 'community': communities[0], 'type': 'text'},
        {'content': 'Naya AI startup Bengaluru mein launch hua! Made in India, powered by Indian talent. 🇮🇳🚀 #TechStartup #MadeInIndia', 'tags': '#Tech #Startup', 'user': users[2], 'community': communities[3], 'type': 'text'},
        {'content': 'Dilli ki galiyon mein ye chole bhature khaaye? Dil khush ho gaya! 😍🍛 Karol Bagh waalon ko pata hoga. #StreetFood #Delhi', 'tags': '#StreetFood #Delhi', 'user': users[0], 'community': communities[2], 'type': 'text'},
        {'content': 'Kal ki Bollywood release ne sabka dil jeet liya! 🎬❤️ Acting, music, sab top class tha! #Bollywood #Cinema', 'tags': '#Bollywood', 'user': users[1], 'community': communities[1], 'type': 'text'},
        {'content': 'Subah ki chai aur ye view — life set hai! ☕🌄 Pahaadon mein trip planning ho rahi hai. #Travel #India', 'tags': '#Travel #Morning', 'user': users[2], 'community': None, 'type': 'text'},
        {'content': 'Har raat 10 minute ki meditation ne meri zindagi badal di. Try karo, guaranteed fayda! 🧘 #Yoga #Wellness', 'tags': '#Yoga #Health', 'user': users[1], 'community': communities[5], 'type': 'text'},
        {'content': 'Yaar, ye meme toh seedha dil pe laga! 😂😂 Hostel waalon ko samajh aayega. #DesiMemes #College', 'tags': '#Memes #Desi', 'user': users[0], 'community': communities[4], 'type': 'text'},
    ]
    all_posts = []
    for pd_item in posts_data:
        p = Post(content=pd_item['content'], tags=pd_item['tags'], user_id=pd_item['user'].id,
                 community_id=pd_item['community'].id if pd_item['community'] else None,
                 post_type=pd_item['type'])
        db.session.add(p)
        all_posts.append(p)
    db.session.flush()

    # Seed likes
    for i, post in enumerate(all_posts):
        for j, user in enumerate(users):
            if (i + j) % 2 == 0:
                like = Like(user_id=user.id, post_id=post.id)
                db.session.add(like)

    # Seed comments
    comment_texts = [
        'Bilkul sahi baat! 👏',
        'Mujhe bhi yahi lagta tha! 🔥',
        'Share karo bhai, sabko dikhana chahiye',
        'Ekdum sahi observation! ✅',
    ]
    for i, post in enumerate(all_posts[:3]):
        c = Comment(content=comment_texts[i % len(comment_texts)],
                    user_id=users[(i+1) % len(users)].id, post_id=post.id)
        db.session.add(c)

    # Seed boards
    board_emojis = [('Cricket Collection', '🏏'), ('Travel Goals', '✈️'), ('Food Bucket List', '🍽️')]
    for be in board_emojis:
        b = Board(name=be[0], emoji=be[1], user_id=users[0].id)
        db.session.add(b)
    db.session.flush()

    db.session.commit()


def random_karma():
    import random
    return random.randint(10, 999)


# ─── Auth Routes ─────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('feed'))
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter(
            (User.phone == identifier) | (User.username == identifier)
        ).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash(f'Swagat hai {user.username}! 🙏', 'success')
            return redirect(url_for('feed'))
        flash('Phone/Username ya password galat hai. Dobara try karo! ❌', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('feed'))
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        bio = request.form.get('bio', '').strip()
        upi = request.form.get('upi', '').strip()

        if User.query.filter_by(phone=phone).first():
            flash('Ye phone number pehle se registered hai! 📵', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Ye username pehle se liya hua hai! 🚫', 'error')
            return redirect(url_for('register'))

        user = User(phone=phone, username=username, bio=bio, upi_id=upi,
                    avatar_seed=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        session['new_user'] = True
        flash(f'Welcome to Zero Touch App, {username}! 🎉', 'success')
        return redirect(url_for('feed'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Phir milenge! 👋', 'info')
    return redirect(url_for('login'))


# ─── Main Feed (Gram) ────────────────────────────────────────────

@app.route('/')
@login_required
def feed():
    filter_type = request.args.get('filter', 'latest')
    community_id = request.args.get('community')

    query = Post.query
    if community_id:
        query = query.filter_by(community_id=community_id)
    if filter_type == 'latest':
        posts = query.order_by(Post.timestamp.desc()).limit(30).all()
    elif filter_type == 'popular':
        posts = sorted(query.all(), key=lambda p: p.score, reverse=True)[:30]
    elif filter_type == 'following':
        cu = current_user()
        followed_ids = [u.id for u in cu.followed.all()]
        posts = query.filter(Post.user_id.in_(followed_ids)).order_by(Post.timestamp.desc()).limit(30).all()
    else:
        posts = query.order_by(Post.timestamp.desc()).limit(30).all()

    communities = Community.query.order_by(Community.name).all()
    cu = current_user()
    liked_ids = {like.post_id for like in Like.query.filter_by(user_id=cu.id).all()}
    return render_template('index.html', posts=posts, communities=communities,
                           filter_type=filter_type, liked_ids=liked_ids)


# ─── Tez (Trending) ─────────────────────────────────────────────

@app.route('/tez')
@login_required
def trending():
    category = request.args.get('cat', 'all')
    category_map = {
        'cricket': '#Cricket',
        'cinema': '#Bollywood',
        'food': '#StreetFood',
        'tech': '#Tech',
        'memes': '#Memes',
    }
    query = Post.query
    if category in category_map:
        query = query.filter(Post.tags.contains(category_map[category]))

    all_posts = query.all()
    posts = sorted(all_posts, key=lambda p: p.score, reverse=True)[:20]
    cu = current_user()
    liked_ids = {like.post_id for like in Like.query.filter_by(user_id=cu.id).all()}
    return render_template('trending.html', posts=posts, category=category, liked_ids=liked_ids)


# ─── Saaj (Boards) ──────────────────────────────────────────────

@app.route('/saaj')
@login_required
def boards():
    cu = current_user()
    my_boards = Board.query.filter_by(user_id=cu.id).all()
    # Discovery: posts with images for the masonry grid
    image_posts = Post.query.filter(Post.image_url != None).order_by(Post.timestamp.desc()).limit(30).all()
    all_posts = Post.query.order_by(Post.timestamp.desc()).limit(40).all()
    return render_template('boards.html', my_boards=my_boards, image_posts=image_posts, all_posts=all_posts)


@app.route('/saaj/create-board', methods=['POST'])
@login_required
def create_board():
    cu = current_user()
    name = request.form.get('name', '').strip()
    emoji = request.form.get('emoji', '📌')
    if name:
        board = Board(name=name, emoji=emoji, user_id=cu.id)
        db.session.add(board)
        db.session.commit()
        flash(f'Board "{name}" banaya gaya! 📌', 'success')
    return redirect(url_for('boards'))


@app.route('/saaj/pin/<int:post_id>', methods=['POST'])
@login_required
def pin_post(post_id):
    cu = current_user()
    board_id = request.form.get('board_id')
    board = Board.query.filter_by(id=board_id, user_id=cu.id).first_or_404()
    existing = Pin.query.filter_by(post_id=post_id, board_id=board.id).first()
    if not existing:
        pin = Pin(post_id=post_id, board_id=board.id)
        db.session.add(pin)
        db.session.commit()
        flash('Post pin ho gaya! 📌', 'success')
    return redirect(request.referrer or url_for('boards'))


# ─── Reel (Shorts) ──────────────────────────────────────────────

@app.route('/reel')
@login_required
def reels():
    video_posts = Post.query.filter(
        (Post.post_type == 'reel') | (Post.video_url != None)
    ).order_by(Post.timestamp.desc()).limit(20).all()
    # Also grab regular posts to fill the page if videos are few
    all_posts = Post.query.order_by(Post.timestamp.desc()).limit(20).all()
    cu = current_user()
    liked_ids = {like.post_id for like in Like.query.filter_by(user_id=cu.id).all()}
    return render_template('reels.html', video_posts=video_posts, all_posts=all_posts, liked_ids=liked_ids)


# ─── Samaj (Communities) ─────────────────────────────────────────

@app.route('/samaj')
@login_required
def communities():
    all_communities = Community.query.all()
    cu = current_user()
    joined_ids = {c.id for c in cu.communities}
    return render_template('communities.html', communities=all_communities, joined_ids=joined_ids)


@app.route('/samaj/<int:community_id>')
@login_required
def community_detail(community_id):
    community = Community.query.get_or_404(community_id)
    posts = Post.query.filter_by(community_id=community.id).order_by(Post.timestamp.desc()).all()
    cu = current_user()
    liked_ids = {like.post_id for like in Like.query.filter_by(user_id=cu.id).all()}
    is_member = cu in community.members.all()
    return render_template('community_detail.html', community=community, posts=posts,
                           liked_ids=liked_ids, is_member=is_member)


@app.route('/samaj/join/<int:community_id>', methods=['POST'])
@login_required
def join_community(community_id):
    community = Community.query.get_or_404(community_id)
    cu = current_user()
    if cu not in community.members.all():
        community.members.append(cu)
        n = Notification(user_id=community.creator_id, actor_id=cu.id,
                         message=f'{cu.username} aapke samaj "{community.name}" se jud gaya!',
                         link=url_for('community_detail', community_id=community.id))
        db.session.add(n)
    else:
        community.members.remove(cu)
    db.session.commit()
    return redirect(request.referrer or url_for('communities'))


@app.route('/samaj/create', methods=['POST'])
@login_required
def create_community():
    cu = current_user()
    name = request.form.get('name', '').strip().replace(' ', '')
    desc = request.form.get('description', '').strip()
    emoji = request.form.get('emoji', '🌐')
    if name and not Community.query.filter_by(name=name).first():
        c = Community(name=name, description=desc, emoji=emoji, creator_id=cu.id)
        c.members.append(cu)
        db.session.add(c)
        db.session.commit()
        flash(f'Samaj "{name}" bana diya! 🎉', 'success')
    else:
        flash('Naam already hai ya khaali nahi hai.', 'error')
    return redirect(url_for('communities'))


# ─── Profile (Pehchaan) ──────────────────────────────────────────

@app.route('/profile')
@app.route('/profile/<username>')
@login_required
def profile(username=None):
    cu = current_user()
    if username is None:
        user = cu
    else:
        user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.timestamp.desc()).all()
    boards = Board.query.filter_by(user_id=user.id).all()
    is_self = cu.id == user.id
    is_following = user in cu.followed.all() if not is_self else False
    liked_ids = {like.post_id for like in Like.query.filter_by(user_id=cu.id).all()}
    return render_template('profile.html', user=user, posts=posts, boards=boards,
                           is_self=is_self, is_following=is_following, liked_ids=liked_ids)


@app.route('/update-profile', methods=['POST'])
@login_required
def edit_profile():
    cu = current_user()

    # Update username (check uniqueness first)
    new_username = request.form.get('username', '').strip()
    if new_username and new_username != cu.username:
        existing = User.query.filter_by(username=new_username).first()
        if existing:
            flash('Yeh username pehle se kisi aur ne liya hai! 🚫', 'error')
            return redirect(url_for('profile'))
        cu.username = new_username

    # Update bio — use empty string if user cleared it
    bio_value = request.form.get('bio', '').strip()
    cu.bio = bio_value

    # Update UPI
    cu.upi_id = request.form.get('upi', '').strip() or None

    # Update avatar seed
    new_seed = request.form.get('avatar_seed', '').strip()
    if new_seed:
        cu.avatar_seed = new_seed

    try:
        db.session.commit()
        flash('Profile update ho gaya! ✅', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Kuch galat hua: {e}', 'error')

    return redirect(url_for('profile'))


# ─── Post Actions ────────────────────────────────────────────────

@app.route('/post', methods=['POST'])
@login_required
def create_post():
    cu = current_user()
    content = request.form.get('content', '').strip()
    image_url = request.form.get('image_url', '').strip() or None
    video_url = request.form.get('video_url', '').strip() or None
    tags = request.form.get('tags', '').strip()
    community_id = request.form.get('community_id') or None

    post_type = 'reel' if video_url else ('image' if image_url else 'text')

    if content:
        post = Post(content=content, image_url=image_url, video_url=video_url,
                    tags=tags, user_id=cu.id, community_id=community_id, post_type=post_type)
        db.session.add(post)
        cu.karma += 5
        db.session.commit()
        flash('Post ho gaya! 🎉', 'success')
    return redirect(request.referrer or url_for('feed'))


@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    cu = current_user()
    post = Post.query.get_or_404(post_id)
    existing = Like.query.filter_by(user_id=cu.id, post_id=post_id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        like = Like(user_id=cu.id, post_id=post_id)
        db.session.add(like)
        post.author.karma += 1
        if post.user_id != cu.id:
            n = Notification(user_id=post.user_id, actor_id=cu.id,
                             message=f'{cu.username} ko aapki post pasand aayi! ❤️',
                             link=url_for('feed'))
            db.session.add(n)
        liked = True
    db.session.commit()
    return jsonify({'liked': liked, 'count': post.like_count})


@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def comment_post(post_id):
    cu = current_user()
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content', '').strip()
    if content:
        comment = Comment(content=content, user_id=cu.id, post_id=post_id)
        db.session.add(comment)
        if post.user_id != cu.id:
            n = Notification(user_id=post.user_id, actor_id=cu.id,
                             message=f'{cu.username} ne aapki post par comment kiya!',
                             link=url_for('feed'))
            db.session.add(n)
        db.session.commit()
        flash('Comment ho gaya! 💬', 'success')
    return redirect(request.referrer or url_for('feed'))


@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    cu = current_user()
    target = User.query.get_or_404(user_id)
    if target.id == cu.id:
        return redirect(request.referrer or url_for('feed'))
    if target in cu.followed.all():
        cu.followed.remove(target)
    else:
        cu.followed.append(target)
        n = Notification(user_id=target.id, actor_id=cu.id,
                         message=f'{cu.username} aapko follow karne laga!',
                         link=url_for('profile', username=cu.username))
        db.session.add(n)
    db.session.commit()
    return redirect(request.referrer or url_for('profile', username=target.username))


# ─── Notifications ───────────────────────────────────────────────

@app.route('/notifications')
@login_required
def notifications():
    cu = current_user()
    notifs = Notification.query.filter_by(user_id=cu.id).order_by(
        Notification.created_at.desc()).limit(30).all()
    # Mark all as read
    for n in notifs:
        n.read = True
    db.session.commit()
    return render_template('notifications.html', notifications=notifs)


@app.route('/api/notification-count')
@login_required
def notification_count():
    cu = current_user()
    count = Notification.query.filter_by(user_id=cu.id, read=False).count()
    return jsonify({'count': count})


# ─── DB Init ─────────────────────────────────────────────────────

with app.app_context():
    db.create_all()
    seed_data()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)