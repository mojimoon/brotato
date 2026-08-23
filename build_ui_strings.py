# -*- coding: utf-8 -*-
"""Generate codex/ui_strings.json: every frontend UI string in 13 languages.

Language order (must match main.py LANGS):
en, fr, zh, ja, ko, zh_TW, ru, pl, es, pt, de, tr, it

The emitted file has:
  - "strings": { key: {lang: text} }      -> used as rawData.ui.<key>
  - "sections": { lang: [ ...ResourcesPanel sections... ] }
"""
import json
from pathlib import Path

LANGS = ['en', 'fr', 'zh', 'ja', 'ko', 'zh_TW', 'ru', 'pl', 'es', 'pt', 'de', 'tr', 'it']

def T(*vals):
    """Build {lang: text} from a 13-tuple in LANGS order."""
    assert len(vals) == len(LANGS), f"expected {len(LANGS)} langs, got {len(vals)}"
    return {lang: v for lang, v in zip(LANGS, vals)}

# ---------------------------------------------------------------------------
# Flat UI strings (the `S` const + a few inline strings)
# ---------------------------------------------------------------------------
strings = {
    # tabs / top-level
    "weapons":            T("Weapons", "Armes", "武器", "武器", "무기", "武器", "Оружие", "Bronie", "Armas", "Armas", "Waffen", "Silahlar", "Armi"),
    "items":              T("Items", "Objets", "物品", "アイテム", "아이템", "物品", "Предметы", "Przedmioty", "Objetos", "Itens", "Gegenstände", "Eşyalar", "Oggetti"),
    "characters":         T("Characters", "Personnages", "角色", "キャラクター", "캐릭터", "角色", "Персонажи", "Postacie", "Personajes", "Personagens", "Charaktere", "Karakterler", "Personaggi"),
    "resources":          T("Resources", "Ressources", "资源", "リソース", "자원", "資源", "Ресурсы", "Zasoby", "Recursos", "Recursos", "Ressourcen", "Kaynaklar", "Risorse"),
    # filters
    "search":             T("Search...", "Rechercher...", "搜索...", "検索...", "검색...", "搜尋...", "Поиск...", "Szukaj...", "Buscar...", "Pesquisar...", "Suchen...", "Ara...", "Cerca..."),
    "all":                T("All", "Tous", "全部", "すべて", "전체", "全部", "Все", "Wszystkie", "Todos", "Todos", "Alle", "Tüm", "Tutti"),
    "tier":               T("Rarity", "Rareté", "稀有度", "レアリティ", "희귀도", "稀有度", "Редкость", "Rzadkość", "Rareza", "Raridade", "Seltenheit", "Nadirlik", "Rarità"),
    "type":               T("Type", "Type", "类型", "タイプ", "유형", "類型", "Тип", "Typ", "Tipo", "Tipo", "Typ", "Tür", "Tipo"),
    "melee":              T("Melee", "Mêlée", "近战", "近接", "근접", "近戰", "Ближний бой", "Walka wręcz", "Cuerpo a cuerpo", "Corpo a corpo", "Nahkampf", "Yakın dövüş", "Mischia"),
    "ranged":             T("Ranged", "À distance", "远战", "遠隔", "원거리", "遠戰", "Дальний бой", "Dystans", "A distancia", "À distância", "Fernkampf", "Menzilli", "A distanza"),
    "set":                T("Set", "Catégorie", "武器类别", "種類", "분류", "類別", "Класс", "Klasa", "Clase", "Classe", "Klasse", "Sınıf", "Classe"),
    "source":             T("Source", "Source", "来源", "入手先", "출처", "來源", "Источник", "Źródło", "Origen", "Origem", "Quelle", "Kaynak", "Fonte"),
    "base":               T("Base", "Base", "本体", "ベース", "기본", "本體", "База", "Podstawa", "Base", "Base", "Basis", "Temel", "Base"),
    "baseGame":           T("Base Game", "Jeu de base", "本体", "基本ゲーム", "기본 게임", "本體", "Основная игра", "Gra podstawowa", "Juego base", "Jogo base", "Basisspiel", "Temel Oyun", "Gioco base"),
    "tag":                T("Tag", "Étiquette", "道具标签", "タグ", "태그", "標籤", "Тег", "Tag", "Etiqueta", "Etiqueta", "Tag", "Etiket", "Etichetta"),
    "sort":               T("Sort", "Trier", "排序", "並び替え", "정렬", "排序", "Сортировка", "Sortuj", "Ordenar", "Ordenar", "Sortieren", "Sırala", "Ordina"),
    "default":            T("Default", "Par défaut", "默认", "デフォルト", "기본", "預設", "По умолчанию", "Domyślnie", "Predeterminado", "Padrão", "Standard", "Varsayılan", "Predefinito"),
    "price":              T("Price", "Prix", "价格", "価格", "가격", "價格", "Цена", "Cena", "Precio", "Preço", "Preis", "Fiyat", "Prezzo"),
    "showPrice":          T("Show Price", "Afficher le prix", "显示价格", "価格を表示", "가격 표시", "顯示價格", "Показать цену", "Pokaż cenę", "Mostrar precio", "Mostrar preço", "Preis anzeigen", "Fiyatı göster", "Mostra prezzo"),
    "on":                 T("On", "Activé", "开", "オン", "켜기", "開", "Вкл", "Wł.", "Activado", "Ligado", "An", "Açık", "Attivo"),
    "off":                T("Off", "Désactivé", "关", "オフ", "끄기", "關", "Выкл", "Wył.", "Desactivado", "Desligado", "Aus", "Kapalı", "Disattivo"),
    # sort options
    "sortDamage":         T("Damage", "Dégâts", "伤害", "ダメージ", "대미지", "傷害", "Урон", "Obrażenia", "Daño", "Dano", "Schaden", "Hasar", "Danni"),
    "sortCrit":           T("Crit", "Crit", "暴击", "クリティカル", "치명타", "暴擊", "Крит", "Crit", "Crít", "Crít", "Crit", "Eleştiri", "Crit"),
    "sortCooldown":       T("Cooldown", "Récupération", "冷却", "クールダウン", "재사용 대기시간", "冷卻", "Перезарядка", "Odstęp", "Enfriamiento", "Recarga", "Abklingzeit", "Bekleme", "Ricarica"),
    "sortRange":          T("Range", "Portée", "范围", "射程", "사거리", "範圍", "Дальность", "Zasięg", "Alcance", "Alcance", "Reichweite", "Menzil", "Gittata"),
    # stat short labels
    "damage":             T("Damage", "Dégâts", "伤害", "ダメージ", "대미지", "傷害", "Урон", "Obrażenia", "Daño", "Dano", "Schaden", "Hasar", "Danni"),
    "crit":               T("Crit", "Crit", "暴击", "クリティカル", "치명타", "暴擊", "Крит", "Crit", "Crít", "Crít", "Crit", "Eleştiri", "Crit"),
    "cooldown":           T("Cooldown", "Récupération", "冷却", "クールダウン", "재사용 대기시간", "冷卻", "Перезарядка", "Odstęp", "Enfriamiento", "Recarga", "Abklingzeit", "Bekleme", "Ricarica"),
    "knockback":          T("Knockback", "Recul", "击退", "ノックバック", "넉백", "擊退", "Отбрасывание", "Odrzut", "Empuje", "Recuo", "Rückstoß", "Geri itme", "Respingimento"),
    "range":              T("Range", "Portée", "范围", "射程", "사거리", "範圍", "Дальность", "Zasięg", "Alcance", "Alcance", "Reichweite", "Menzil", "Gittata"),
    "accuracy":           T("Accuracy", "Précision", "命中率", "命中率", "명중률", "命中率", "Меткость", "Celność", "Precisión", "Precisão", "Genauigkeit", "İsabet", "Precisione"),
    "lifesteal":          T("Lifesteal", "Vol de vie", "生命窃取", "ライフスティール", "생명력 흡수", "生命竊取", "Кража жизни", "Kradzież życia", "Robo de vida", "Roubo de vida", "Lebensdiebstahl", "Can çalma", "Rubavita"),
    "piercing":           T("Piercing", "Perforation", "贯通", "貫通", "관통", "貫通", "Пробивание", "Przebijanie", "Perforación", "Perfuração", "Durchdringung", "Delme", "Perforazione"),
    "bounce":             T("Bounce", "Rebond", "反弹", "バウンス", "바운스", "反彈", "Отскок", "Odbicie", "Rebote", "Ricochete", "Abpraller", "Sekme", "Rimbalzo"),
    "projectiles":        T("Projectiles", "Projectiles", "投射物", "投射物", "투사체", "投射物", "Снаряды", "Pociski", "Proyectiles", "Projéteis", "Projektile", "Mermiler", "Proiettili"),
    "dmg":                T("dmg", "dmg", "伤害", "ダメージ", "대미지", "傷害", "урон", "obr.", "daño", "dano", "Schad", "hasar", "danni"),
    "dps":                T("DPS", "DPS", "DPS", "DPS", "DPS", "DPS", "DPS", "DPS", "DPS", "DPS", "DPS", "DPS", "DPS"),
    "basePrice":          T("Base Price", "Prix de base", "基础价格", "基本価格", "기본 가격", "基礎價格", "Базовая цена", "Cena bazowa", "Precio base", "Preço base", "Basispreis", "Temel fiyat", "Prezzo base"),
    "perWave":            T("/wave", "/vague", "/波", "/ウェーブ", "/웨이브", "每波", "/волна", "/fala", "/ronda", "/onda", "/Welle", "/dalga", "/onda"),
    "wave":               T("Wave", "Vague", "波次", "ウェーブ", "웨이브", "波次", "Волна", "Fala", "Ronda", "Onda", "Welle", "Dalga", "Onda"),
    # detail panel
    "effects":            T("Effects", "Effets", "效果", "効果", "효과", "效果", "Эффекты", "Efekty", "Efectos", "Efeitos", "Effekte", "Etkiler", "Effetti"),
    "startingWeapons":    T("Starting Weapons", "Armes de départ", "起始武器", "初期武器", "시작 무기", "起始武器", "Стартовое оружие", "Bronie początkowe", "Armas iniciales", "Armas iniciais", "Startwaffen", "Başlangıç silahları", "Armi iniziali"),
    "preferredTags":      T("Preferred Tags", "Étiquettes préférées", "偏好标签", "推奨タグ", "선호 태그", "偏好標籤", "Предпочитаемые теги", "Preferowane tagi", "Etiquetas preferidas", "Etiquetas preferidas", "Bevorzugte Tags", "Tercih edilen etiketler", "Etichette preferite"),
    "unique":             T("Unique", "Unique", "独特", "ユニーク", "고유", "獨特", "Уникальный", "Unikalny", "Único", "Único", "Einzigartig", "Benzersiz", "Unico"),
    "limited":            T("Limited", "Limité", "限制", "制限", "제한", "限制", "Ограниченный", "Ograniczony", "Limitado", "Limitado", "Begrenzt", "Sınırlı", "Limitato"),
    "clickToSee":         T("Click to see details", "Cliquez pour voir les détails", "点击左侧查看详情", "左をクリックして詳細を表示", "왼쪽을 클릭하여 세부 정보 보기", "點擊左側查看詳細", "Нажмите, чтобы увидеть подробности", "Kliknij, aby zobaczyć szczegóły", "Haz clic para ver detalles", "Clique para ver detalhes", "Klicken Sie für Details", "Ayrıntılar için tıklayın", "Clicca per vedere i dettagli"),
    "belowNightmare":     T("Danger 5", "Danger 5", "难5", "難易度5", "위험 5", "難5", "Опасность 5", "Niebezpieczeństwo 5", "Peligro 5", "Perigo 5", "Gefahr 5", "Tehlike 5", "Pericolo 5"),
    "nightmare":          T("Nightmare", "Cauchemar", "噩梦", "ナイトメア", "나이트메어", "噩夢", "Кошмар", "Koszmar", "Pesadilla", "Pesadelo", "Albtraum", "Kâbus", "Incubo"),
    "basePriceShort":     T("Price", "Prix", "价格", "価格", "가격", "價格", "Цена", "Cena", "Precio", "Preço", "Preis", "Fiyat", "Prezzo"),
    "belowNightmareShort":T("D5", "D5", "难5", "難5", "위험5", "難5", "О5", "N5", "P5", "P5", "G5", "T5", "P5"),
    "nightmareShort":     T("NM", "CM", "噩梦", "NM", "NM", "噩夢", "КМ", "K", "PN", "PD", "AT", "K", "I"),
    # attack speed calc
    "attackSpeedCalc":    T("Attack Speed Calculator", "Calculateur de vitesse d'attaque", "攻速计算器", "攻撃速度計算機", "공격 속도 계산기", "攻速計算機", "Калькулятор скорости атаки", "Kalkulator szybkości ataku", "Calculadora de velocidad de ataque", "Calculadora de velocidade de ataque", "Angriffsgeschwindigkeitsrechner", "Saldırı hızı hesaplayıcı", "Calcolatore velocità d'attacco"),
    "attackSpeed":        T("A.Spd", "Vit. Atq", "攻速", "攻速", "공속", "攻速", "Ск. атаки", "Szyb. atk", "Vel. Atq", "Vel. Atq", "Angr.-Tempo", "Sal. Hız", "Vel. Att"),
    "statRange":          T("Range", "Portée", "范围", "射程", "사거리", "範圍", "Дальность", "Zasięg", "Alcance", "Alcance", "Reichweite", "Menzil", "Gittata"),
    "attackSpeedBreakpoints": T("A.Spd Breakpoints", "Seuils de vit. atq", "攻速断点", "攻撃速度ブレイクポイント", "공격 속도 분기점", "攻速斷點", "Контрольные точки скорости атаки", "Punkty szybkości ataku", "Puntos de vel. atq", "Pontos de vel. atq", "Angriffsschwellen", "Saldırı hızı kırılım noktaları", "Soglie vel. att"),
    "curse":              T("Curse", "Malédiction", "诅咒", "呪い", "저주", "詛咒", "Проклятие", "Klątwa", "Maldición", "Maldição", "Fluch", "Lanet", "Maledizione"),
    "clear":              T("Clear Filters", "Effacer les filtres", "清除筛选", "フィルターをクリア", "필터 지우기", "清除篩選", "Очистить фильтры", "Wyczyść filtry", "Borrar filtros", "Limpar filtros", "Filter löschen", "Filtreleri temizle", "Cancella filtri"),
    "weaponCount":        T("#Weapon", "#Arme", "武器数量", "武器数", "무기 수", "武器數量", "№ Оружие", "#Bronie", "#Arma", "#Arma", "#Waffe", "#Silah", "#Arma"),
    "frames":             T("Frames", "Images", "帧数", "フレーム", "프레임", "幀數", "Кадры", "Klatki", "Fotogramas", "Quadros", "Frames", "Kare", "Frame"),
    "tooltipCooldown":    T("Tooltip Cooldown", "Récupération (info)", "显示冷却", "ツールチップクールダウン", "툴팁 재사용", "顯示冷卻", "Перезарядка (подсказка)", "Odstęp (podpowiedź)", "Enfriamiento (información)", "Recarga (dica)", "Abklingzeit (Tooltip)", "İpucu bekleme", "Ricarica (tooltip)"),
    "actualCooldown":     T("Actual Cooldown", "Récupération (réelle)", "实际冷却", "実際実際のクールダウン", "실제 재사용", "實際冷卻", "Фактическая перезарядка", "Odstęp (rzeczywisty)", "Enfriamiento real", "Recarga real", "Tatsächliche Abklingzeit", "Gerçek bekleme", "Ricarica reale"),
    "tooltip":            T("Tooltip", "Info", "显示", "ツールチップ", "툴팁", "顯示", "Подсказка", "Podpowiedź", "Información", "Dica", "Tooltip", "İpucu", "Tooltip"),
    "actual":             T("Actual", "Réelle", "实际", "実際", "실제", "實際", "Фактически", "Rzeczywisty", "Real", "Real", "Tatsächlich", "Gerçek", "Reale"),
    "rangeInfo":          T(
        "Player range stat. Actual bonus is halved (e.g. 150 base range + 100 range stat → 200 weapon range)",
        "La statistique de portée du joueur. Le bonus réel est divisé par deux (ex. 150 portée de base + 100 en portée → 200 portée d'arme)",
        "玩家范围属性。实际加成减半（例如，150基础范围 + 100范围属性 → 200武器范围）",
        "プレイヤーの射程ステータス。実際のボーナスは半減します（例：基本射程150 + 射程ステータス100 → 武器射程200）",
        "플레이어 사거리 능력치. 실제 보너스는 절반으로 감소합니다 (예: 기본 사거리 150 + 사거리 능력치 100 → 무기 사거리 200)",
        "玩家範圍屬性。實際加成減半（例如，150基礎範圍 + 100範圍屬性 → 200武器範圍）",
        "Характеристика дальности игрока. Фактический бонус уменьшается вдвое (напр. базовая дальность 150 + 100 дальности → дальность оружия 200)",
        "Statystyka zasięgu gracza. Faktyczna premia jest o połowę mniejsza (np. 150 bazowego zasięgu + 100 ze statystyki → 200 zasięgu broni)",
        "Estadística de alcance del jugador. La bonificación real se reduce a la mitad (p. ej. 150 alcance base + 100 de alcance → 200 alcance de arma)",
        "Estatística de alcance do jogador. O bônus real é reduzido pela metade (ex. 150 alcance base + 100 de alcance → 200 alcance da arma)",
        "Reichweitenwert des Spielers. Der tatsächliche Bonus halbiert sich (z. B. 150 Basisreichweite + 100 Reichweite → 200 Waffenreichweite)",
        "Oyuncu menzil değeri. Gerçek bonus yarıya düşer (ör. 150 taban menzil + 100 menzil → 200 silah menzili)",
        "Statistica di gittata del giocatore. Il bonus effettivo è dimezzato (es. 150 gittata base + 100 gittata → 200 gittata arma)",
    ),
    # ResourcesPanel inline strings
    "about":              T("About", "À propos", "关于", "について", "정보", "關於", "О нас", "O nas", "Acerca de", "Sobre", "Über", "Hakkında", "Informazioni"),
    "aboutText":          T(
        "If you find this helpful, please consider giving me a star on GitHub! Thank you!",
        "Si cela vous aide, n'hésitez pas à me mettre une étoile sur GitHub ! Merci !",
        "如果你觉得这个有帮助，请考虑在 GitHub 上给我点个 star！谢谢！",
        "役に立ったと思ったら、GitHubでスターをいただけると嬉しいです！ありがとうございます！",
        "도움이 되셨다면 GitHub에 별을 눌러주세요! 감사합니다!",
        "如果你覺得這個有幫助，請考慮在 GitHub 上給我點個 star！謝謝！",
        "Если вам помогло, поставьте мне звезду на GitHub! Спасибо!",
        "Jeśli to pomaga, rozważ zostawienie gwiazdki na GitHubie! Dziękuję!",
        "Si te resulta útil, ¡considera darme una estrella en GitHub! ¡Gracias!",
        "Se isto for útil, considere me dar uma estrela no GitHub! Obrigado!",
        "Wenn dir das hilft, gib mir gerne einen Stern auf GitHub! Danke!",
        "Yararlı bulursanız GitHub'da yıldız vermeyi düşünün! Teşekkürler!",
        "Se ti è utile, considera di mettermi una stella su GitHub! Grazie!",
    ),
    "tryMods":            T("Try out my Brotato mods:", "Essayez mes mods Brotato :", "试试我的 Brotato 模组：", "私のBrotatoMODを試してみてください：", "제 Brotato 모드를 사용해 보세요:", "試試我的 Brotato 模組：", "Попробуйте мои моды Brotato:", "Wypróbuj moje mody do Brotato:", "Prueba mis mods de Brotato:", "Experimente meus mods de Brotato:", "Probier meine Brotato-Mods aus:", "Brotato modlarımı deneyin:", "Prova i miei mod di Brotato:"),
    "modCurse":           T("Cursed & Double Sided Upgrades [DoubleSidedUpgrades]", "Cursed & Double Sided Upgrades [DoubleSidedUpgrades]", "诅咒和双面升级 [DoubleSidedUpgrades]", "Cursed & Double Sided Upgrades [DoubleSidedUpgrades]", "Cursed & Double Sided Upgrades [DoubleSidedUpgrades]", "詛咒和雙面升級 [DoubleSidedUpgrades]", "Cursed & Double Sided Upgrades [DoubleSidedUpgrades]", "Cursed & Double Sided Upgrades [DoubleSidedUpgrades]", "Cursed & Double Sided Upgrades [DoubleSidedUpgrades]", "Cursed & Double Sided Upgrades [DoubleSidedUpgrades]", "Cursed & Double Sided Upgrades [DoubleSidedUpgrades]", "Cursed & Double Sided Upgrades [DoubleSidedUpgrades]", "Cursed & Double Sided Upgrades [DoubleSidedUpgrades]"),
    "modOneItem":         T("One Item to Rule Them All [OneItemToRuleThemAll]", "One Item to Rule Them All [OneItemToRuleThemAll]", "所有物品变为同一个 [OneItemToRuleThemAll]", "One Item to Rule Them All [OneItemToRuleThemAll]", "One Item to Rule Them All [OneItemToRuleThemAll]", "所有物品變為同一個 [OneItemToRuleThemAll]", "One Item to Rule Them All [OneItemToRuleThemAll]", "One Item to Rule Them All [OneItemToRuleThemAll]", "One Item to Rule Them All [OneItemToRuleThemAll]", "One Item to Rule Them All [OneItemToRuleThemAll]", "One Item to Rule Them All [OneItemToRuleThemAll]", "One Item to Rule Them All [OneItemToRuleThemAll]", "One Item to Rule Them All [OneItemToRuleThemAll]"),
    # cooldown / reload calculator strings
    "cooldownIs":         T("Cooldown is", "Temps de recharge", "每发射{shots}次冷却为", "リロード毎{shots}回のクールダウン", "장전 {shots}회마다 쿨타임", "每發射{shots}次冷卻為", "Перезарядка", "Odstęp przeładowania", "Enfriamiento", "Recarga", "Abklingzeit", "Bekleme süresi", "Ricarica"),
    # cooldownEvery is the TRAILING "every N shots" phrase. For languages whose
    # cooldownIs already embeds {shots} at the front (zh/ja/ko/zh_TW) this is empty.
    "cooldownEvery":      T(" every {shots} shots", " toutes les {shots} attaques", "", "", "", "", " каждые {shots} выстрелов", " co {shots} strzałów", " cada {shots} disparos", " a cada {shots} tiros", " alle {shots} Schüsse", " her {shots} atışta", " ogni {shots} colpi"),
    "everyShotsColon":    T("every {shots} shots:", "toutes les {shots} attaques :", "每发射{shots}次:", "リロード毎{shots}回:", "장전 {shots}회마다:", "每發射{shots}次:", "каждые {shots} выстрелов:", "co {shots} strzałów:", "cada {shots} disparos:", "a cada {shots} tiros:", "alle {shots} Schüsse:", "her {shots} atışta:", "ogni {shots} colpi:"),
    "equiv":              T("equiv", "équiv", "等效", "相当", "상당", "等效", "экв", "odpow", "equiv", "equiv", "äquiv", "eşdeğ", "equiv"),
    "attackThrust":       T("(Thrust)", "(Estoc)", "(突刺)", "(突き)", "(찌르기)", "(突刺)", "(Выпад)", "(Pchnięcie)", "(Embestida)", "(Estocada)", "(Stich)", "(Saplama)", "(Spinta)"),
    "attackSweep":        T("(Sweep)", "(Fauchage)", "(横扫)", "(薙ぎ)", "(휩쓸기)", "(橫掃)", "(Размаx)", "(Zamiatanie)", "(Barrido)", "(Varredura)", "(Schwung)", "(Süpürme)", "(Falcio)"),
}

# ---------------------------------------------------------------------------
# ResourcesPanel sections (share structure; only title/label translated)
# ---------------------------------------------------------------------------
# Translate the descriptive English labels. Brand/proper nouns stay identical.
SECTION_LABELS = {
    "Special Thanks": T("Special Thanks", "Remerciements spéciaux", "特别感谢", "特別感谢", "특별 감사", "特別感謝", "Особая благодарность", "Specjalne podziękowania", "Agradecimientos especiales", "Agradecimentos especiais", "Besonderer Dank", "Özel teşekkürler", "Ringraziamenti speciali"),
    "Resources":      T("Resources", "Ressources", "资源", "リソース", "자원", "資源", "Ресурсы", "Zasoby", "Recursos", "Recursos", "Ressourcen", "Kaynaklar", "Risorse"),
    "Community":      T("Community", "Communauté", "社区", "コミュニティ", "커뮤니티", "社區", "Сообщество", "Społeczność", "Comunidad", "Comunidade", "Community", "Topluluk", "Comunità"),
    "Official":       T("Official", "Officiel", "官方", "公式", "공식", "官方", "Официальное", "Oficjalne", "Oficial", "Oficial", "Offiziell", "Resmî", "Ufficiale"),
    "DPS Calculator": T("DPS Calculator", "Calculatrice DPS", "DPS 计算器", "DPS計算機", "DPS 계산기", "DPS 計算機", "Расчёт DPS", "Kalkulator DPS", "Calculadora de DPS", "Calculadora de DPS", "DPS-Rechner", "DPS Hesaplayıcı", "Calcolatore DPS"),
    "Item Efficiency":T("Item Efficiency", "Efficacité des objets", "物品性价比", "アイテム効率", "아이템 효율", "物品性價比", "Эффективность предметов", "Wydajność przedmiotów", "Eficiencia de objetos", "Eficiência de itens", "Gegenstandseffizienz", "Eşya verimliliği", "Efficienza oggetti"),
    "Misc Calculators":T("Misc Calculators", "Calculatrices diverses", "杂项计算器", "その他計算機", "기타 계산기", "雜項計算機", "Прочие калькуляторы", "Różne kalkulatory", "Calculadoras varias", "Calculadoras diversas", "Verschiedene Rechner", "Çeşitli hesaplayıcılar", "Calcolatori vari"),
    "Enemy Calculator":T("Enemy Calculator", "Calculatrice d'ennemis", "敌人计算器", "敵計算機", "적 계산기", "敵人計算機", "Калькулятор врагов", "Kalkulator wrogów", "Calculadora de enemigos", "Calculadora de inimigos", "Feind-Rechner", "Düşman hesaplayıcı", "Calcolatore nemici"),
    "Endless Mode":   T("Endless Mode", "Mode Infini", "无尽模式", "エンドレスモード", "무한 모드", "無盡模式", "Бесконечный режим", "Tryb nieskończony", "Modo infinito", "Modo infinito", "Endlos-Modus", "Sonsuz mod", "Modalità infinita"),
    "Weapons":        T("Weapons", "Armes", "武器", "武器", "무기", "武器", "Оружие", "Bronie", "Armas", "Armas", "Waffen", "Silahlar", "Armi"),
    "Characters":     T("Characters", "Personnages", "角色", "キャラクター", "캐릭터", "角色", "Персонажи", "Postacie", "Personajes", "Personagens", "Charaktere", "Karakterler", "Personaggi"),
    "Items":          T("Items", "Objets", "物品", "アイテム", "아이템", "物品", "Предметы", "Przedmioty", "Objetos", "Itens", "Gegenstände", "Eşyalar", "Oggetti"),
    "Stats":          T("Stats", "Statistiques", "属性", "ステータス", "능력치", "屬性", "Характеристики", "Statystyki", "Estadísticas", "Estatísticas", "Werte", "İstatistikler", "Statistiche"),
    "Enemies":        T("Enemies", "Ennemis", "敌人", "敵", "적", "敵人", "Враги", "Wrogowie", "Enemigos", "Inimigos", "Feinde", "Düşmanlar", "Nemici"),
}

# Build per-language section arrays from a template (urls/brands constant).
def build_sections(lang):
    L = lambda en: SECTION_LABELS[en][lang]
    return [
        {
            "key": "thanks", "icon": "Star", "title": L("Special Thanks"),
            "items": [
                {
                    "brand": "sheets", "subBrand": "sheets", "label": "Brotato MultiTool", "by": "AroRIsing",
                    "url": "https://docs.google.com/spreadsheets/d/1qi_KWBH_fQlrXJioDGJQScuRbwfndHzLu4Zj5Ek0Aso/edit?gid=1643867668",
                    "sub": [
                        {"icon": "sheets", "label": L("DPS Calculator"), "url": "https://docs.google.com/spreadsheets/d/1qi_KWBH_fQlrXJioDGJQScuRbwfndHzLu4Zj5Ek0Aso/edit?gid=1374380662"},
                        {"icon": "sheets", "label": L("Item Efficiency"), "url": "https://docs.google.com/spreadsheets/d/1qi_KWBH_fQlrXJioDGJQScuRbwfndHzLu4Zj5Ek0Aso/edit?gid=743336370"},
                        {"icon": "sheets", "label": L("Misc Calculators"), "url": "https://docs.google.com/spreadsheets/d/1qi_KWBH_fQlrXJioDGJQScuRbwfndHzLu4Zj5Ek0Aso/edit?gid=1779030030"},
                        {"icon": "sheets", "label": L("Enemy Calculator"), "url": "https://docs.google.com/spreadsheets/d/1qi_KWBH_fQlrXJioDGJQScuRbwfndHzLu4Zj5Ek0Aso/edit?gid=647636409"},
                        {"icon": "sheets", "label": L("Endless Mode"), "url": "https://docs.google.com/spreadsheets/d/1qi_KWBH_fQlrXJioDGJQScuRbwfndHzLu4Zj5Ek0Aso/edit?gid=1720835033"},
                    ],
                },
                {"brand": "steam", "label": "Improved Tooltip", "by": "WL", "url": "https://steamcommunity.com/sharedfiles/filedetails/?id=3019195689"},
            ],
        },
        {
            "key": "resources", "icon": "Files", "title": L("Resources"),
            "items": [
                {
                    "brand": "wiki", "subBrand": "wiki", "label": "Wiki",
                    "url": "https://brotato.wiki.spellsandguns.com/Brotato_Wiki",
                    "sub": [
                        {"icon": "weapon", "label": L("Weapons"), "url": "https://brotato.wiki.spellsandguns.com/Weapons"},
                        {"icon": "character", "label": L("Characters"), "url": "https://brotato.wiki.spellsandguns.com/Characters"},
                        {"icon": "item", "label": L("Items"), "url": "https://brotato.wiki.spellsandguns.com/Items"},
                        {"icon": "stat", "label": L("Stats"), "url": "https://brotato.wiki.spellsandguns.com/Stats"},
                        {"icon": "enemy", "label": L("Enemies"), "url": "https://brotato.wiki.spellsandguns.com/Enemies"},
                        {"icon": "community", "label": L("Community"), "url": "https://brotato.wiki.spellsandguns.com/Community"},
                    ],
                },
            ],
        },
        {
            "key": "community", "icon": "ChatDotRound", "title": L("Community"),
            "items": [
                {"brand": "discord", "label": "Discord", "url": "https://discord.com/invite/j39jE6k"},
                {"brand": "reddit", "label": "Reddit", "url": "https://www.reddit.com/r/Brotato"},
            ],
        },
        {
            "key": "official", "icon": "OfficeBuilding", "title": L("Official"),
            "items": [
                {"brand": "steam", "label": "Steam", "url": "https://store.steampowered.com/app/1942280/Brotato"},
                {"brand": "x", "label": "X", "url": "https://x.com/Studio_Evil"},
                {"brand": "bilibili", "label": "Bilibili", "url": "https://space.bilibili.com/3546576049932887"},
            ],
        },
    ]

sections = {lang: build_sections(lang) for lang in LANGS}

out = {"strings": strings, "sections": sections}

CODEX_DIR = Path(__file__).resolve().parent
out_path = CODEX_DIR / "ui_strings.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

print(f"Wrote {out_path}")
print(f"  strings: {len(strings)} keys x {len(LANGS)} langs")
print(f"  sections: {len(sections)} langs")
