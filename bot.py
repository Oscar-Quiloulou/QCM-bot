import discord
from discord.ext import commands, tasks
from discord import app_commands
import sqlite3
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import time, timezone, timedelta

# --- 1. LOGS DISQUE OPTIMISÉS (Max 2 Mo) ---
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(filename='bot.log', maxBytes=2*1024*1024, backupCount=1, encoding='utf-8')
logger.addHandler(handler)

# --- CONFIGURATION DISCORD ---
TOKEN = je met le token apres  # Remplacez par votre token Discord
PENDING_CHANNEL_ID = 1557067124751732917  # ⚠️ Remplacez par l'ID du salon de validation Admin
QUIZ_CHANNEL_ID = 1565327428413296710     # ⚠️ REMPLACEZ par l'ID du salon où poster les quiz à 8h et 18h

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
DB_FILE = "qcm_database.db"
MAX_HISTORY_ROWS = 2000

# --- 2. BASE DE DONNÉES SQLite ---
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA auto_vacuum=FULL;")
        cursor.execute("PRAGMA page_size=4096;")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                option1 TEXT NOT NULL,
                option2 TEXT NOT NULL,
                option3 TEXT NOT NULL,
                correct_idx INTEGER NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                score INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

# --- HELPER : BARRE DE PROGRESSION XP ---
def make_xp_bar(current_xp: int, max_xp: int = 50, length: int = 10) -> str:
    filled = int((current_xp / max_xp) * length)
    bar = "▰" * filled + "▱" * (length - filled)
    return f"`[{bar}]` **{current_xp}/{max_xp} XP**"

# --- CHECK ADMIN ---
def is_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        has_admin_perm = interaction.user.guild_permissions.administrator
        has_admin_role = any(role.name == "Admin" for role in interaction.user.roles)
        
        if has_admin_perm or has_admin_role:
            return True
        
        await interaction.response.send_message("❌ Vous devez posséder le rôle `@Admin` pour cette commande.", ephemeral=True)
        return False
    return app_commands.check(predicate)

# --- PURGE AUTOMATIQUE ---
@tasks.loop(hours=24)
async def auto_clean_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            DELETE FROM history 
            WHERE id NOT IN (
                SELECT id FROM history ORDER BY id DESC LIMIT {MAX_HISTORY_ROWS}
            )
        ''')
        conn.commit()
        cursor.execute("VACUUM;")
        conn.commit()

def add_user_xp(user_id: str, xp_to_add: int = 10, lvl_to_add: int = 0):
    leveled_up = False
    new_lvl = 1
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT xp, level FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row:
            current_xp, current_lvl = row
            new_xp = current_xp + xp_to_add
            new_lvl = current_lvl + lvl_to_add
            
            while new_xp >= 50:
                new_xp -= 50
                new_lvl += 1
                leveled_up = True
                
            cursor.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ?", (new_xp, new_lvl, user_id))
        else:
            new_xp = xp_to_add
            new_lvl = 1 + lvl_to_add
            while new_xp >= 50:
                new_xp -= 50
                new_lvl += 1
                leveled_up = True
            cursor.execute("INSERT INTO users (user_id, xp, level) VALUES (?, ?, ?)", (user_id, new_xp, new_lvl))
        conn.commit()

    return leveled_up, new_lvl, new_xp

# --- VUE DU SALON D'APPROBATION ADMIN ---
class QuestionApprovalView(discord.ui.View):
    def __init__(self, question_text: str, options: list, correct_idx: int, author: discord.User):
        super().__init__(timeout=None)
        self.question_text = question_text
        self.options = options
        self.correct_idx = correct_idx
        self.author = author

    @discord.ui.button(label="✅ Valider", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        has_admin_perm = interaction.user.guild_permissions.administrator
        has_admin_role = any(role.name == "Admin" for role in interaction.user.roles)
        if not (has_admin_perm or has_admin_role):
            await interaction.response.send_message("❌ Seul un membre du rôle `@Admin` peut valider cette question.", ephemeral=True)
            return

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO questions (question, option1, option2, option3, correct_idx) VALUES (?, ?, ?, ?, ?)",
                (self.question_text, self.options[0], self.options[1], self.options[2], self.correct_idx)
            )
            conn.commit()

        for item in self.children:
            item.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ Question Approuvée et Enregistrée"
        embed.set_footer(text=f"Validé par {interaction.user.display_name}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        has_admin_perm = interaction.user.guild_permissions.administrator
        has_admin_role = any(role.name == "Admin" for role in interaction.user.roles)
        if not (has_admin_perm or has_admin_role):
            await interaction.response.send_message("❌ Seul un membre du rôle `@Admin` peut refuser cette question.", ephemeral=True)
            return

        for item in self.children:
            item.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "❌ Question Refusée"
        embed.set_footer(text=f"Refusé par {interaction.user.display_name}")
        await interaction.response.edit_message(embed=embed, view=self)

# --- MODAL PROPOSITION DE QUESTION ---
class AddQuestionModal(discord.ui.Modal, title="Proposer une question QCM"):
    question_input = discord.ui.TextInput(label="Question", style=discord.TextStyle.paragraph, required=True)
    option1 = discord.ui.TextInput(label="Réponse 1", required=True)
    option2 = discord.ui.TextInput(label="Réponse 2", required=True)
    option3 = discord.ui.TextInput(label="Réponse 3", required=True)
    correct_option = discord.ui.TextInput(label="Numéro vraie réponse (1, 2 ou 3)", min_length=1, max_length=1, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            correct_idx = int(self.correct_option.value) - 1
            if correct_idx not in [0, 1, 2]:
                raise ValueError()
        except ValueError:
            await interaction.response.send_message("❌ Numéro de bonne réponse invalide. Entrez 1, 2 ou 3.", ephemeral=True)
            return

        options_list = [self.option1.value, self.option2.value, self.option3.value]
        channel = interaction.guild.get_channel(PENDING_CHANNEL_ID)

        if not channel:
            await interaction.response.send_message("❌ Salon de validation introuvable. Contactez un Admin.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📩 Nouvelle proposition de Question QCM",
            description=f"**Proposée par :** {interaction.user.mention}\n\n**Question :**\n{self.question_input.value}",
            color=discord.Color.gold()
        )
        opts_formatted = "\n".join([f"{'✅' if i == correct_idx else '❌'} {opt}" for i, opt in enumerate(options_list)])
        embed.add_field(name="Propositions :", value=opts_formatted, inline=False)

        view = QuestionApprovalView(
            question_text=self.question_input.value,
            options=options_list,
            correct_idx=correct_idx,
            author=interaction.user
        )

        await channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Question envoyée pour validation à l'administration !", ephemeral=True)

# --- PANEL ADMIN (/QCM) ---
class AdminPanelControl(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📋 Questions", style=discord.ButtonStyle.primary)
    async def list_questions(self, interaction: discord.Interaction, button: discord.ui.Button):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, question, option1, option2, option3, correct_idx FROM questions")
            questions = cursor.fetchall()

        if not questions:
            await interaction.response.send_message("Aucune question dans la BDD.", ephemeral=True)
            return

        embed = discord.Embed(title="📚 Questions enregistrées", color=discord.Color.blue())
        for q_id, q_txt, o1, o2, o3, c_idx in questions:
            opts = [o1, o2, o3]
            formatted_opts = "\n".join([f"{'✅' if i == c_idx else '❌'} {opt}" for i, opt in enumerate(opts)])
            embed.add_field(name=f"#{q_id} — {q_txt}", value=formatted_opts, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📊 Stats", style=discord.ButtonStyle.success)
    async def stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        total_members = interaction.guild.member_count if interaction.guild else 0
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM history")
            total_responded = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM history")
            total_attempts = cursor.fetchone()[0]

        pct = (total_responded / total_members * 100) if total_members > 0 else 0
        embed = discord.Embed(title="📊 Participation au QCM", color=discord.Color.green())
        embed.add_field(name="Membres uniques ayant répondu", value=f"**{total_responded}** / {total_members} ({pct:.1f}%)", inline=False)
        embed.add_field(name="Total de réponses enregistrées", value=str(total_attempts), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⏰ Heures des réponses", style=discord.ButtonStyle.secondary)
    async def response_times(self, interaction: discord.Interaction, button: discord.ui.Button):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, score, timestamp FROM history ORDER BY id DESC LIMIT 10")
            recent = cursor.fetchall()

        if not recent:
            await interaction.response.send_message("Historique vide.", ephemeral=True)
            return

        embed = discord.Embed(title="⏰ 10 dernières participations", color=discord.Color.gold())
        logs = []
        for uid, score, ts in recent:
            member = interaction.guild.get_member(int(uid)) if interaction.guild else None
            name = member.display_name if member else f"ID: {uid}"
            logs.append(f"• **{name}** — {ts} (Score: {score})")

        embed.description = "\n".join(logs)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⭐ Modifier XP/Level", style=discord.ButtonStyle.danger)
    async def edit_xp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("💡 Utilisez la commande `/donner_xp` pour créditer un membre avec son `@` !", ephemeral=True)

# --- VUE DU JEU MULTI-JOUEURS (POUR PUBLICATION AUTO & MANUAL) ---
class MultiUserQCMView(discord.ui.View):
    def __init__(self, q_id: int, options: list, correct_idx: int):
        super().__init__(timeout=None)  # Pas de timeout pour que les membres puissent répondre toute la journée
        self.q_id = q_id
        self.options = options
        self.correct_idx = correct_idx
        self.answered_users = set()

        prefixes = ["A. ", "B. ", "C. "]
        for idx, option_text in enumerate(options):
            btn = discord.ui.Button(
                label=f"{prefixes[idx]}{option_text}",
                custom_id=f"quiz_{q_id}_{idx}",
                style=discord.ButtonStyle.secondary
            )
            btn.callback = self.make_callback(idx)
            self.add_item(btn)

    def make_callback(self, chosen_idx: int):
        async def callback(interaction: discord.Interaction):
            user_id = str(interaction.user.id)

            if user_id in self.answered_users:
                await interaction.response.send_message("❌ Vous avez déjà répondu à ce quiz !", ephemeral=True)
                return

            self.answered_users.add(user_id)
            is_correct = (chosen_idx == self.correct_idx)
            score = 1 if is_correct else 0

            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO history (user_id, score) VALUES (?, ?)", (user_id, score))
                conn.commit()

            if is_correct:
                leveled_up, new_lvl, new_xp = add_user_xp(user_id, xp_to_add=10)
                msg = f"🎉 **Bonne réponse !** You gagnez **+10 XP**.\n{make_xp_bar(new_xp)}"
                if leveled_up:
                    msg += f"\n🎊 **LEVEL UP !** Vous passez au **Niveau {new_lvl}** !"
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                good_answer = f"{chr(65 + self.correct_idx)}. {self.options[self.correct_idx]}"
                await interaction.response.send_message(f"❌ **Mauvaise réponse.** La bonne réponse était **{good_answer}**.", ephemeral=True)

        return callback

# --- TÂCHE PROGRAMMÉE DE PUBLICATION À 08:00 ET 18:00 ---
# UTC offset adapté (France = UTC+1 en hiver / UTC+2 en été). Ajustez la heure selon votre fuseau.
publish_times = [
    time(hour=8, minute=0, tzinfo=timezone.utc),
    time(hour=18, minute=0, tzinfo=timezone.utc)
]

async def publish_daily_quiz():
    """Fonction qui tire une question au hasard et l'envoie dans le salon dédié."""
    channel = bot.get_channel(QUIZ_CHANNEL_ID)
    if not channel:
        print("❌ Salon de publication Quiz introuvable !")
        return

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, question, option1, option2, option3, correct_idx FROM questions ORDER BY RANDOM() LIMIT 1")
        q = cursor.fetchone()

    if not q:
        print("❌ Aucune question en BDD à publier.")
        return

    q_id, q_text, o1, o2, o3, correct_idx = q
    options = [o1, o2, o3]

    embed = discord.Embed(
        title="🔔 Quiz du Moment !",
        description=f"### {q_text}\n\nCliquez sur un bouton ci-dessous pour tester votre culture générale et gagner de l'XP !",
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Question #{q_id} | Posté automatiquement")

    view = MultiUserQCMView(q_id=q_id, options=options, correct_idx=correct_idx)
    await channel.send(content="📢 @quiz C'est l'heure du QCM !", embed=embed, view=view)

@tasks.loop(time=publish_times)
async def scheduled_quiz_loop():
    await publish_daily_quiz()

# --- COMMANDES SLASH DISCORD ---
@bot.event
async def on_ready():
    auto_clean_db.start()
    if not scheduled_quiz_loop.is_running():
        scheduled_quiz_loop.start()
    await bot.tree.sync()
    print(f"Bot démarré et prêt : {bot.user}")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Vous devez posséder le rôle `@Admin` pour utiliser cette commande.", ephemeral=True)

# 1. Panel Admin
@bot.tree.command(name="qcm", description="Ouvre le panel de configuration Admin")
@is_admin()
async def qcm_admin(interaction: discord.Interaction):
    embed = discord.Embed(title="⚙️ Panel de Configuration QCM", color=discord.Color.dark_purple())
    await interaction.response.send_message(embed=embed, view=AdminPanelControl(), ephemeral=True)

# 2. Forcer/Tester la publication immédiate du Quiz du moment (Rôle Admin)
@bot.tree.command(name="tester_publication", description="Publie immédiatement une question dans le salon Quiz")
@is_admin()
async def force_publish(interaction: discord.Interaction):
    await interaction.response.send_message("🚀 Publication manuelle en cours...", ephemeral=True)
    await publish_daily_quiz()

# 3. Donner de l'XP
@bot.tree.command(name="donner_xp", description="Ajouter de l'XP ou des Niveaux à un membre")
@app_commands.describe(membre="Sélectionnez le membre", xp="Quantité d'XP", niveau="Nombre de niveaux")
@is_admin()
async def donner_xp(interaction: discord.Interaction, membre: discord.Member, xp: int = 0, niveau: int = 0):
    add_user_xp(str(membre.id), xp_to_add=xp, lvl_to_add=niveau)
    await interaction.response.send_message(f"✅ **{xp} XP** et **{niveau} Niveau(x)** ajoutés à {membre.mention} !", ephemeral=True)

# 4. Import JSON par lot
@bot.tree.command(name="importer_questions", description="Ajouter des questions par lot au format JSON")
@is_admin()
async def importer_questions(interaction: discord.Interaction, données_json: str):
    try:
        questions_list = json.loads(données_json)
        if not isinstance(questions_list, list):
            raise ValueError("Le JSON doit être une liste [ ... ]")

        count = 0
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            for item in questions_list:
                q_text = item.get("q") or item.get("question")
                opts = item.get("opts") or item.get("options")
                correct_idx = item.get("c") if "c" in item else item.get("correct")

                if q_text and isinstance(opts, list) and len(opts) >= 3 and correct_idx in [0, 1, 2]:
                    cursor.execute(
                        "INSERT INTO questions (question, option1, option2, option3, correct_idx) VALUES (?, ?, ?, ?, ?)",
                        (q_text, opts[0], opts[1], opts[2], int(correct_idx))
                    )
                    count += 1
            conn.commit()

        await interaction.response.send_message(f"✅ **{count} questions** importées dans SQLite !", ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f"❌ Format JSON invalide.\nDétails : `{str(e)}`", ephemeral=True)

# 5. Proposer une question
@bot.tree.command(name="ajouter_question", description="Proposer une question pour le QCM")
async def add_question_command(interaction: discord.Interaction):
    await interaction.response.send_modal(AddQuestionModal())

# 6. Jouer au QCM individuel
@bot.tree.command(name="play_qcm", description="Répondre à une question du QCM")
async def play_qcm(interaction: discord.Interaction):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, question, option1, option2, option3, correct_idx FROM questions ORDER BY RANDOM() LIMIT 1")
        q = cursor.fetchone()

    if not q:
        await interaction.response.send_message("❌ Aucune question disponible.", ephemeral=True)
        return

    q_id, q_text, o1, o2, o3, correct_idx = q
    options = [o1, o2, o3]

    view = MultiUserQCMView(q_id=q_id, options=options, correct_idx=correct_idx)
    embed = discord.Embed(
        title="❓ Question QCM",
        description=f"### {q_text}",
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"Question #{q_id}")
    await interaction.response.send_message(embed=embed, view=view)

# 7. Profil Joueur
@bot.tree.command(name="profil", description="Afficher le profil QCM et les stats d'un membre")
@app_commands.describe(membre="Le membre dont vous souhaitez voir le profil (Optionnel)")
async def user_profile(interaction: discord.Interaction, membre: discord.Member = None):
    target = membre or interaction.user
    uid = str(target.id)

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT xp, level FROM users WHERE user_id = ?", (uid,))
        user_row = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*), SUM(score) FROM history WHERE user_id = ?", (uid,))
        stats_row = cursor.fetchone()
        
        cursor.execute("""
            SELECT user_id, (SELECT COUNT(*) FROM users u2 WHERE u2.level > u1.level OR (u2.level = u1.level AND u2.xp > u1.xp)) + 1 AS rank
            FROM users u1 WHERE user_id = ?
        """, (uid,))
        rank_row = cursor.fetchone()

    xp = user_row[0] if user_row else 0
    level = user_row[1] if user_row else 1
    rank = rank_row[1] if rank_row else "N/A"
    
    total_played = stats_row[0] if stats_row and stats_row[0] else 0
    total_wins = stats_row[1] if stats_row and stats_row[1] else 0
    win_rate = (total_wins / total_played * 100) if total_played > 0 else 0.0

    embed = discord.Embed(
        title=f"👤 Profil QCM — {target.display_name}",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="🏆 Rang", value=f"**#{rank}** sur le serveur", inline=True)
    embed.add_field(name="⭐ Niveau", value=f"**Niveau {level}**", inline=True)
    embed.add_field(name="⚡ Progression", value=make_xp_bar(xp), inline=False)
    embed.add_field(name="🎯 Parties jouées", value=f"**{total_played}** partie(s)", inline=True)
    embed.add_field(name="✅ Bonnes réponses", value=f"**{total_wins}** ({win_rate:.1f}%)", inline=True)

    await interaction.response.send_message(embed=embed)

# 8. Classement
@bot.tree.command(name="classement", description="Affiche le classement des joueurs par XP/Niveau")
async def leaderboard(interaction: discord.Interaction):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, xp, level FROM users ORDER BY level DESC, xp DESC LIMIT 10")
        rows = cursor.fetchall()

    if not rows:
        await interaction.response.send_message("Aucun membre n'a encore d'XP.", ephemeral=True)
        return

    embed = discord.Embed(title="🏆 Classement des Joueurs", color=discord.Color.gold())
    text = ""
    medals = ["🥇", "🥈", "🥉"]
    for rank, (uid, xp, level) in enumerate(rows, start=1):
        member = interaction.guild.get_member(int(uid)) if interaction.guild else None
        pseudo = member.display_name if member else f"Inconnu ({uid})"
        prefix = medals[rank-1] if rank <= 3 else f"**#{rank}**"
        text += f"{prefix} | **{pseudo}** — Niv. **{level}** ({xp} XP)\n"

    embed.description = text
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
