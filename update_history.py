# -*- coding: utf-8 -*-
"""Balance update history (official patch notes since 1.2.0.0, cross-checked with game files).

Two outputs, built by main.py through build_history():
  - per-entry history  {entry id | weapon family id: [{v, lines}]}  -> detail panels
  - mechanics history  [{v, lines}]                                  -> resources page

Entry ops (ENTRY_HISTORY):
  ('snap', old_ref, new_ref)  diff effects / weapon stats / max_nb between two codex data
                              snapshots (git refs of this repo; 'cur' = data being built)
  ('eff', match, old)         current effect (key or text_key == match) vs. a copy with the
                              `old` overrides (dotted keys, e.g. 'extra.value2'), re-rendered
  ('add_eff', match)          effect added
  ('del_eff', effect)         effect removed (raw effect dict, rendered)
  ('start', add, remove)      starting weapon options (ids)
  ('ban', add)                items that no longer appear for the character
  ('no_upgrade', stat)        level-up option no longer offered
  ('start_for', chars)        weapon became a starting option for these characters
  ('new',)                    added to the game
  ('note', N(...))            free text, 13 languages; {@KEY} -> game translation of KEY

Patch notes: other_mods/update_log.txt. Where the notes and the game files disagree, the files
win (e.g. Hiker 1.2.0.0: 5 -> 6 materials every 10 steps). Corrected notes: docs/official-patch-notes-1.2.md.
1.2.0.2-beta0 / beta1 are merged into 1.2.0.2, 1.2.0.4-beta0 / beta1 into 1.2.0.4. Enemy changes and bug fixes are left out.
"""
import copy
import difflib
import json
import re
import subprocess
from pathlib import Path

CODEX_DIR = Path(__file__).resolve().parent
LANGS = ['en', 'fr', 'zh', 'ja', 'ko', 'zh_TW', 'ru', 'pl', 'es', 'pt', 'de', 'tr', 'it']
ROMAN = ['I', 'II', 'III', 'IV']

# codex data snapshots (git tags of this repo) by game version
SNAP_1201 = 'v3.4.0'   # 1.2.0.1
SNAP_1202 = 'v3.6.0'   # 1.2.0.2


def N(**kw):
    assert set(kw) == set(LANGS), sorted(set(LANGS) ^ set(kw))
    return kw


# ---------------------------------------------------------------------------
# Per-entry history (newest version first in the output; order here is free)
# ---------------------------------------------------------------------------
FARTHEST = N(
    en='Now targets the farthest enemy in range instead of the closest and keeps tracking it during the swing, so each attack sweeps through more enemies',
    fr="Vise désormais l'ennemi le plus éloigné à portée au lieu du plus proche et le suit pendant le coup, pour balayer plus d'ennemis à chaque attaque",
    zh='现在优先瞄准攻击范围内最远的敌人而非最近的敌人，并在挥击过程中持续追踪目标，每次攻击能扫中更多敌人',
    ja='射程内で最も近い敵ではなく最も遠い敵を狙い、振っている間も追尾するようになり、1回の攻撃でより多くの敵を巻き込む',
    ko='이제 사거리 내 가장 가까운 적이 아닌 가장 먼 적을 노리고 휘두르는 동안 계속 추적해, 한 번 공격할 때 더 많은 적을 맞힘',
    zh_TW='現在優先瞄準攻擊範圍內最遠的敵人而非最近的敵人，並在揮擊過程中持續追蹤目標，每次攻擊能掃中更多敵人',
    ru='Теперь целится в самого дальнего врага в радиусе, а не в ближайшего, и следит за ним во время взмаха, поэтому каждая атака задевает больше врагов',
    pl='Celuje teraz w najdalszego wroga w zasięgu zamiast najbliższego i śledzi go podczas zamachu, więc każdy atak trafia więcej wrogów',
    es='Ahora apunta al enemigo más lejano dentro del alcance en vez del más cercano y lo sigue durante el golpe, para barrer más enemigos en cada ataque',
    pt='Agora mira o inimigo mais distante no alcance em vez do mais próximo e o acompanha durante o golpe, atingindo mais inimigos a cada ataque',
    de='Zielt jetzt auf den entferntesten statt den nächsten Gegner in Reichweite und verfolgt ihn während des Schwungs, damit jeder Angriff mehr Gegner trifft',
    tr='Artık menzildeki en yakın yerine en uzak düşmanı hedefler ve savuruş boyunca onu takip eder; her saldırı daha fazla düşmana çarpar',
    it='Ora mira al nemico più lontano entro la gittata invece del più vicino e lo segue durante il colpo, così ogni attacco travolge più nemici',
)
NOMECA = N(
        en='No longer drops Mecha Fruits and cannot pick up those dropped by other players',
        fr='Ne fait plus apparaître de fruits méca et ne peut plus ramasser ceux des autres joueurs',
        zh='不再掉落机械果，也无法拾取其他玩家掉落的机械果',
        ja='メカの果実を落とさなくなり、他のプレイヤーが落としたものも拾えない',
        ko='더 이상 기계 열매가 떨어지지 않으며 다른 플레이어가 떨어뜨린 것도 주울 수 없음',
        zh_TW='不再掉落機械果，也無法拾取其他玩家掉落的機械果',
        ru='Механические плоды больше не выпадают, и подбирать выпавшие у других игроков нельзя',
        pl='Nie wypadają już owoce mecha i nie można podnosić tych upuszczonych przez innych graczy',
        es='Ya no aparecen frutas meca y no puede recoger las que suelten otros jugadores',
        pt='Não dropa mais frutas meca e não pode pegar as que outros jogadores deixarem',
        de='Lässt keine Mecha-Früchte mehr fallen und kann die anderer Spieler nicht aufheben',
        tr='Artık mekanik meyve düşürmez ve diğer oyuncuların düşürdüklerini de alamaz',
        it='Non fa più cadere frutti meca e non può raccogliere quelli degli altri giocatori',
    )

ENTRY_HISTORY = [
    # ---- 1.2.0.0 ----
    ('1.2.0.0', 'character_diver', [('eff', 'enemy_health', {'value': 250})]),
    ('1.2.0.0', 'character_druid', [('eff', 'enemy_fruit_drops', {'value': 3})]),
    ('1.2.0.0', 'character_dwarf', [('eff', 'EFFECT_GAIN_STAT_WHEN_ATTACK_KILLED_ENEMIES', {'extra.value2': 6})]),
    ('1.2.0.0', 'character_hiker', [
        ('eff', 'EFFECT_GOLD_ON_EVERY_STEP', {'value': 5}),
        ('del_eff', {'key': 'stat_speed', 'text_key': '', 'value': -5, 'custom_key': '',
                     'storage_method': 0, 'effect_sign': 3, 'extra': {}}),
    ]),
    ('1.2.0.0', 'character_farmer', [('add_eff', 'item_garden')]),
    ('1.2.0.0', 'character_fisherman', [('eff', 'enemy_gold_drops', {'value': -50})]),
    ('1.2.0.0', 'character_beast_master', [('add_eff', 'item_ratzilla')]),
    ('1.2.0.0', 'character_one_arm', [('add_eff', 'weapon_set_bonus')]),

    # ---- 1.2.0.2 (beta0 + beta1) ----
    ('1.2.0.2', 'character_variant', [('snap', SNAP_1201, SNAP_1202)]),
    ('1.2.0.2', 'character_time_shifter', [('no_upgrade', 'stat_dodge')]),
    ('1.2.0.2', 'character_arsonist', [('no_upgrade', 'stat_engineering')]),
    ('1.2.0.2', 'character_generalist', [('start', [], ['weapon_molotov_1'])]),
    ('1.2.0.2', 'character_mad_scientist', [('start', ['weapon_laser_gun_1', 'weapon_carbon_bow_1'],
                                             ['weapon_awl_1', 'weapon_blowgun_1'])]),
    ('1.2.0.2', 'character_one_arm', [('start', [], ['weapon_boomerang_1'])]),
    ('1.2.0.2', 'character_wounded', [('ban', ['item_pocket_watch'])]),
    ('1.2.0.2', 'item_chimera_cells', [('new',)]),
    ('1.2.0.2', 'item_wildfire_mutation', [('note', N(
        en='Now unlocked by default (was the reward for winning a run with {@CHARACTER_MUTANT})',
        fr='Désormais débloqué par défaut (auparavant récompense d\'une victoire avec {@CHARACTER_MUTANT})',
        zh='改为默认解锁（原为使用{@CHARACTER_MUTANT}通关的奖励）',
        ja='最初から解放されるようになった（以前は{@CHARACTER_MUTANT}でクリアした報酬）',
        ko='이제 기본으로 해금됨 (이전: {@CHARACTER_MUTANT}(으)로 승리 시 보상)',
        zh_TW='改為預設解鎖（原為使用{@CHARACTER_MUTANT}通關的獎勵）',
        ru='Теперь открыт по умолчанию (раньше — награда за победу за {@CHARACTER_MUTANT})',
        pl='Teraz odblokowany domyślnie (wcześniej nagroda za wygraną postacią {@CHARACTER_MUTANT})',
        es='Ahora desbloqueado por defecto (antes era la recompensa por ganar con {@CHARACTER_MUTANT})',
        pt='Agora desbloqueado por padrão (antes era a recompensa por vencer com {@CHARACTER_MUTANT})',
        de='Jetzt standardmäßig freigeschaltet (zuvor Belohnung für einen Sieg mit {@CHARACTER_MUTANT})',
        tr='Artık varsayılan olarak açık (önceden {@CHARACTER_MUTANT} ile kazanma ödülüydü)',
        it='Ora sbloccato di default (prima era la ricompensa per una vittoria con {@CHARACTER_MUTANT})',
    ))]),
    ('1.2.0.2', 'item_meca_evolved_leap', [('snap', SNAP_1201, SNAP_1202)]),
    ('1.2.0.2', 'item_mut_evolved_leap', [('snap', SNAP_1201, SNAP_1202)]),
] + [
    ('1.2.0.2', f'item_fossil_{p}', [('snap', SNAP_1201, SNAP_1202)])
    for p in ('tooth', 'right_arm', 'left_leg', 'right_leg', 'spine', 'jaw', 'left_arm', 'skull')
] + [
    # ---- 1.2.0.3 ----
    ('1.2.0.3', 'character_caveman', [('start', [], ['weapon_boomerang_1'])]),

    # ---- 1.2.0.4-beta0 ----
    ('1.2.0.4', 'weapon_carbon_bow', [
        ('snap', SNAP_1202, 'cur'),
        ('start_for', ['character_engineer', 'character_well_rounded']),
        ('note', N(
            en='When cursed, its burning damage and landmine damage are now boosted too',
            fr='Une fois maudit, ses dégâts de brûlure et de mine sont désormais aussi augmentés',
            zh='被诅咒时，燃烧伤害和地雷伤害现在也会提高',
            ja='呪われた時、燃焼ダメージと地雷のダメージも強化されるようになった',
            ko='저주받으면 이제 화상 대미지와 지뢰 대미지도 강화됨',
            zh_TW='被詛咒時，燃燒傷害和地雷傷害現在也會提高',
            ru='Под проклятием теперь также усиливается урон от горения и мин',
            pl='Po przeklęciu wzmacniane są teraz także obrażenia od podpalenia i min',
            es='Al estar maldito, ahora también aumenta su daño de quemadura y el de las minas',
            pt='Quando amaldiçoado, o dano de queimadura e o dano das minas agora também aumentam',
            de='Wenn verflucht, werden jetzt auch Brand- und Minenschaden verstärkt',
            tr='Lanetlendiğinde artık yanma hasarı ve mayın hasarı da güçlenir',
            it='Quando maledetto, ora aumentano anche i danni da ustione e delle mine',
        )),
    ]),
    ('1.2.0.4', 'weapon_boomerang', [
        ('snap', SNAP_1202, 'cur'),
        ('start_for', ['character_wildling']),
    ]),
    ('1.2.0.4', 'weapon_tranq_rifle', [('snap', SNAP_1202, 'cur')]),
    ('1.2.0.4', 'weapon_molotov', [
        ('snap', SNAP_1202, 'cur'),
        ('note', N(
            en='Fire pool size doubled at every tier',
            fr='Taille de la flaque de feu doublée à tous les rangs',
            zh='所有级别的火焰池大小翻倍',
            ja='全ランクで炎の水たまりのサイズが2倍に',
            ko='모든 등급에서 불웅덩이 크기 2배',
            zh_TW='所有級別的火焰池大小翻倍',
            ru='Размер огненной лужи удвоен на всех уровнях',
            pl='Rozmiar kałuży ognia podwojony na wszystkich poziomach',
            es='El tamaño del charco de fuego se duplica en todos los niveles',
            pt='O tamanho da poça de fogo dobra em todos os níveis',
            de='Größe der Feuerlache auf allen Stufen verdoppelt',
            tr='Tüm seviyelerde ateş birikintisinin boyutu iki katına çıktı',
            it='Dimensione della pozza di fuoco raddoppiata a ogni livello',
        )),
        ('note', N(
            en='With piercing, every enemy the projectile passes through leaves a fire pool',
            fr='Avec la perforation, chaque ennemi traversé par le projectile laisse une flaque de feu',
            zh='拥有穿透时，投射物穿过的每个敌人都会留下一个火焰池',
            ja='貫通があると、弾が貫いた敵ごとに炎の水たまりが残る',
            ko='관통이 있으면 투사체가 지나간 적마다 불웅덩이가 생김',
            zh_TW='擁有穿透時，投射物穿過的每個敵人都會留下一個火焰池',
            ru='С пробиванием каждый пробитый снарядом враг оставляет огненную лужу',
            pl='Z przebiciem każdy przebity wróg zostawia kałużę ognia',
            es='Con perforación, cada enemigo atravesado por el proyectil deja un charco de fuego',
            pt='Com perfuração, cada inimigo atravessado pelo projétil deixa uma poça de fogo',
            de='Mit Durchschlag hinterlässt jeder durchbohrte Gegner eine Feuerlache',
            tr='Delme varken merminin içinden geçtiği her düşman bir ateş birikintisi bırakır',
            it='Con la perforazione, ogni nemico attraversato dal proiettile lascia una pozza di fuoco',
        )),
    ]),
    ('1.2.0.4', 'weapon_sticky_grenade', [
        ('snap', SNAP_1202, 'cur'),
        ('note', N(
            en='With piercing, the grenade sticks to every enemy it passes through and keeps flying',
            fr='Avec la perforation, la grenade se colle à chaque ennemi traversé et poursuit sa course',
            zh='拥有穿透时，手雷会粘在穿过的每个敌人身上并继续飞行',
            ja='貫通があると、貫いた敵すべてにグレネードが付着し、そのまま飛び続ける',
            ko='관통이 있으면 수류탄이 지나간 적마다 달라붙고 계속 날아감',
            zh_TW='擁有穿透時，手榴彈會黏在穿過的每個敵人身上並繼續飛行',
            ru='С пробиванием граната прилипает к каждому пробитому врагу и летит дальше',
            pl='Z przebiciem granat przykleja się do każdego przebitego wroga i leci dalej',
            es='Con perforación, la granada se pega a cada enemigo que atraviesa y sigue volando',
            pt='Com perfuração, a granada gruda em cada inimigo atravessado e continua voando',
            de='Mit Durchschlag haftet die Granate an jedem durchbohrten Gegner und fliegt weiter',
            tr='Delme varken el bombası içinden geçtiği her düşmana yapışır ve uçmaya devam eder',
            it='Con la perforazione, la granata si attacca a ogni nemico attraversato e prosegue',
        )),
    ]),
    ('1.2.0.4', 'weapon_flail', [
        ('snap', SNAP_1202, 'cur'),
        ('note', N(
            en='Larger hitbox (taller), and the guaranteed-crit zone at the tip is 20% bigger',
            fr='Zone de frappe agrandie (plus haute) et zone de critique garanti au bout 20 % plus grande',
            zh='攻击判定区域纵向增大，末端必定暴击的判定区域扩大20%',
            ja='攻撃判定が縦に拡大し、先端の確定クリティカル範囲が20%拡大',
            ko='공격 판정이 세로로 커지고, 끝부분의 확정 치명타 범위가 20% 확대',
            zh_TW='攻擊判定區域縱向增大，末端必定暴擊的判定區域擴大20%',
            ru='Зона поражения выше, а зона гарантированного крита на конце больше на 20%',
            pl='Większy (wyższy) obszar trafienia, a strefa pewnego trafienia krytycznego na końcu jest o 20% większa',
            es='Zona de impacto más alta y la zona de crítico garantizado en la punta es un 20% mayor',
            pt='Área de acerto mais alta, e a zona de crítico garantido na ponta é 20% maior',
            de='Größere (höhere) Trefferzone, die Zone für garantierte Krits an der Spitze ist 20% größer',
            tr='Vuruş alanı dikeyde büyüdü, uçtaki kesin kritik alanı %20 genişledi',
            it='Area di colpo più alta e la zona di critico garantito sulla punta è più grande del 20%',
        )),
    ]),
    ('1.2.0.4', 'item_chimera_cells', [('snap', SNAP_1202, 'cur')]),
    ('1.2.0.4', 'character_engineer', [('start', ['weapon_carbon_bow_1'], [])]),
    ('1.2.0.4', 'character_well_rounded', [('start', ['weapon_carbon_bow_1'], [])]),
    ('1.2.0.4', 'character_wildling', [('start', ['weapon_boomerang_1'], ['weapon_flail_1'])]),
    ('1.2.0.4', 'character_caveman', [('note', N(
        en='As long as at least one weapon is ignited, the fog does not thicken in the next wave',
        fr='Tant qu\'au moins une arme est enflammée, le brouillard ne s\'épaissit pas à la vague suivante',
        zh='只要点燃了至少一把武器，下一波的迷雾就不会继续变浓',
        ja='武器を1つ以上点火していれば、次のウェーブで霧が濃くならない',
        ko='무기를 하나 이상 점화하면 다음 웨이브에 안개가 더 짙어지지 않음',
        zh_TW='只要點燃了至少一把武器，下一波的迷霧就不會繼續變濃',
        ru='Пока подожжено хотя бы одно оружие, туман в следующей волне не сгущается',
        pl='Dopóki co najmniej jedna broń jest podpalona, mgła nie gęstnieje w następnej fali',
        es='Mientras al menos un arma esté encendida, la niebla no se espesa en la siguiente oleada',
        pt='Enquanto ao menos uma arma estiver acesa, a névoa não fica mais densa na próxima onda',
        de='Solange mindestens eine Waffe entzündet ist, wird der Nebel in der nächsten Welle nicht dichter',
        tr='En az bir silah tutuşturulduğu sürece sis bir sonraki dalgada yoğunlaşmaz',
        it='Finché almeno un\'arma è accesa, la nebbia non si infittisce nell\'ondata successiva',
    ))]),
    # ---- 1.2.0.4-beta1 ----
    ('1.2.0.4', 'weapon_whip', [('note', FARTHEST)]),
    ('1.2.0.4', 'weapon_flail', [('note', FARTHEST)]),
    ('1.2.0.4', 'weapon_crowbar', [('snap', SNAP_1202, 'cur')]),
    ('1.2.0.4', 'weapon_awl', [('snap', SNAP_1202, 'cur')]),
    ('1.2.0.4', 'weapon_sticky_grenade', [
        ('note', N(
            en='Bounces off the arena edges instead of exploding outside the playable area',
            fr="Rebondit sur les bords de l'arène au lieu d'exploser hors de la zone jouable",
            zh='现在会从场地边界反弹，而不是落到可游玩区域外爆炸',
            ja='プレイエリア外で爆発せず、アリーナの端で跳ね返るようになった',
            ko='플레이 영역 밖에서 폭발하지 않고 경기장 가장자리에서 튕겨 나옴',
            zh_TW='現在會從場地邊界反彈，而不是落到可遊玩區域外爆炸',
            ru='Отскакивает от краёв арены, а не взрывается за пределами игровой зоны',
            pl='Odbija się od krawędzi areny zamiast wybuchać poza obszarem gry',
            es='Rebota en los bordes de la arena en lugar de explotar fuera de la zona jugable',
            pt='Ricocheteia nas bordas da arena em vez de explodir fora da área jogável',
            de='Prallt am Arenarand ab, statt außerhalb des Spielbereichs zu explodieren',
            tr='Oynanabilir alanın dışında patlamak yerine arena kenarlarından seker',
            it="Rimbalza sui bordi dell'arena invece di esplodere fuori dall'area di gioco",
        )),
    ]),
    ('1.2.0.4', 'item_lost_organ', [('snap', SNAP_1202, 'cur')]),
    ('1.2.0.4', 'item_sunken_bell', [('snap', SNAP_1202, 'cur')]),
    ('1.2.0.4', 'character_wounded', [('ban', ['item_magma_boots'])]),
    ('1.2.0.4', 'character_bull', [('note', NOMECA)]),
    ('1.2.0.4', 'character_beast_master', [('note', NOMECA)]),
    ('1.2.0.4', 'character_hiker', [('start', ['weapon_spoon_1'], ['weapon_meat_tenderizer_1'])]),
    ('1.2.0.4', 'character_one_arm', [('note', N(
        en='Its weapon class bonus can no longer be copied by mutation',
        fr="Son bonus de classe d'arme ne peut plus être copié par la mutation",
        zh='武器类别加成无法再被异变复制',
        ja='武器種類ボーナスが変異でコピーされなくなった',
        ko='무기 분류 보너스를 더 이상 돌연변이로 복제할 수 없음',
        zh_TW='武器類別加成無法再被異變複製',
        ru='Бонус класса оружия больше нельзя скопировать мутацией',
        pl='Premii klasy broni nie da się już skopiować mutacją',
        es='Su bonificación de clase de arma ya no puede copiarse con mutación',
        pt='Seu bônus de classe de arma não pode mais ser copiado pela mutação',
        de='Sein Waffenklassenbonus kann nicht mehr per Mutation kopiert werden',
        tr='Silah sınıfı bonusu artık mutasyonla kopyalanamaz',
        it="Il suo bonus di classe d'arma non può più essere copiato dalla mutazione",
    ))]),
    # ---- 1.2.0.4 release ----
    ('1.2.0.4', 'character_druid', [('start', [], ['weapon_meat_tenderizer_1'])]),
    ('1.2.0.4', 'character_hunter', [('ban', ['item_lost_organ'])]),
    ('1.2.0.4', 'character_knight', [('ban', ['item_lost_organ'])]),
    ('1.2.0.4', 'character_sailor', [('ban', ['item_lost_organ'])]),
    ('1.2.0.4', 'item_dart_trap', [('snap', SNAP_1202, 'cur')]),
    ('1.2.0.4', 'item_bleeding_turret', [('snap', SNAP_1202, 'cur')]),
    ('1.2.0.4', 'character_arsonist', [('note', N(
        en='{@STAT_ELEMENTAL_DAMAGE} and explosive items now appear more often in the shop',
        fr="Les objets de {@STAT_ELEMENTAL_DAMAGE} et explosifs apparaissent plus souvent en boutique",
        zh='{@STAT_ELEMENTAL_DAMAGE}类和爆炸类道具会更频繁地出现在商店中',
        ja='{@STAT_ELEMENTAL_DAMAGE}系と爆発系のアイテムがショップに出やすくなった',
        ko='{@STAT_ELEMENTAL_DAMAGE} 및 폭발 아이템이 상점에 더 자주 등장',
        zh_TW='{@STAT_ELEMENTAL_DAMAGE}類和爆炸類道具會更頻繁地出現在商店中',
        ru='Предметы на {@STAT_ELEMENTAL_DAMAGE} и взрывы чаще появляются в магазине',
        pl='Przedmioty na {@STAT_ELEMENTAL_DAMAGE} i wybuchowe częściej pojawiają się w sklepie',
        es='Los objetos de {@STAT_ELEMENTAL_DAMAGE} y explosivos aparecen más a menudo en la tienda',
        pt='Itens de {@STAT_ELEMENTAL_DAMAGE} e explosivos aparecem com mais frequência na loja',
        de='Gegenstände für {@STAT_ELEMENTAL_DAMAGE} und Explosionen erscheinen öfter im Shop',
        tr='{@STAT_ELEMENTAL_DAMAGE} ve patlayıcı eşyalar mağazada daha sık çıkar',
        it='Gli oggetti di {@STAT_ELEMENTAL_DAMAGE} ed esplosivi compaiono più spesso nel negozio',
    ))]),
    ('1.2.0.4', 'item_pyromaniac', [('note', N(
        en='Burning from pets and turrets now stacks too, just like burning from weapons',
        fr='La brûlure des familiers et des tourelles se cumule désormais aussi, comme celle des armes',
        zh='宠物和炮塔造成的燃烧现在也会像武器造成的燃烧一样叠加',
        ja='ペットとタレットの燃焼も、武器の燃焼と同じように重なるようになった',
        ko='이제 펫과 포탑의 화상도 무기의 화상처럼 중첩됨',
        zh_TW='寵物和砲塔造成的燃燒現在也會像武器造成的燃燒一樣疊加',
        ru='Горение от питомцев и турелей теперь тоже складывается, как от оружия',
        pl='Podpalenie od zwierzaków i wieżyczek teraz też się kumuluje, tak jak od broni',
        es='La quemadura de mascotas y torretas ahora también se acumula, igual que la de las armas',
        pt='A queimadura de mascotes e torretas agora também acumula, como a das armas',
        de='Brand von Haustieren und Geschützen stapelt sich jetzt ebenfalls, wie der von Waffen',
        tr='Evcil hayvan ve taretlerin yanması da artık silahlarınki gibi birikir',
        it="L'ustione di animali e torrette ora si accumula come quella delle armi",
    ))]),
    ('1.2.0.4', 'weapon_cestus', [('note', N(
        en='When cursed, the Knockback needed for double damage now drops to 6–8 instead of rising',
        fr="Une fois maudit, le Recul requis pour doubler les dégâts baisse désormais à 6–8 au lieu d'augmenter",
        zh='被诅咒时，触发双倍伤害所需的击退改为降低到 6–8，不再提高',
        ja='呪われた時、ダメージ2倍に必要なノックバックが上がらず、6～8に下がるようになった',
        ko='저주받으면 대미지 2배에 필요한 넉백이 오르지 않고 6~8로 낮아짐',
        zh_TW='被詛咒時，觸發雙倍傷害所需的擊退改為降低到 6–8，不再提高',
        ru='Под проклятием отбрасывание, нужное для двойного урона, теперь снижается до 6–8, а не растёт',
        pl='Po przeklęciu odrzut potrzebny do podwójnych obrażeń spada teraz do 6–8 zamiast rosnąć',
        es='Al estar maldito, el Retroceso necesario para el doble de daño ahora baja a 6–8 en lugar de subir',
        pt='Quando amaldiçoado, o Repulsão necessário para dano dobrado agora cai para 6–8 em vez de subir',
        de='Wenn verflucht, sinkt der für doppelten Schaden nötige Rückstoß jetzt auf 6–8, statt zu steigen',
        tr='Lanetlendiğinde çift hasar için gereken geri itme artık artmak yerine 6–8\'e düşer',
        it="Quando maledetto, il Contraccolpo necessario per il doppio dei danni ora scende a 6–8 invece di salire",
    ))]),
]


# ---------------------------------------------------------------------------
# Mechanics history (resources page)
# ---------------------------------------------------------------------------
MECH_HISTORY = [
    ('1.2.0.4', [
        N(en='Mutation strength curve: 70% at about 58 {@STAT_EVOLUTION} and 100% at 130 (was 40 and 100); pets, turrets and other effects that need 70% strength become copyable from about 58',
          fr='Courbe de puissance de la mutation : 70 % vers 58 de {@STAT_EVOLUTION} et 100 % à 130 (avant 40 et 100) ; familiers, tourelles et autres effets exigeant 70 % deviennent copiables vers 58',
          zh='异变强度曲线：约58点{@STAT_EVOLUTION}时达到70%，130点时达到100%（原为40点和100点）；宠物、炮塔等需要70%强度的效果约从58点起可以复制',
          ja='変異の強度曲線：{@STAT_EVOLUTION}約58で70%、130で100%（以前は40と100）。ペット・タレットなど強度70%が必要な効果は約58からコピー可能',
          ko='돌연변이 강도 곡선: {@STAT_EVOLUTION} 약 58에서 70%, 130에서 100% (이전 40과 100). 펫, 포탑 등 70% 강도가 필요한 효과는 약 58부터 복제 가능',
          zh_TW='異變強度曲線：約58點{@STAT_EVOLUTION}時達到70%，130點時達到100%（原為40點和100點）；寵物、砲塔等需要70%強度的效果約從58點起可以複製',
          ru='Кривая силы мутации: 70% примерно при 58 ед. {@STAT_EVOLUTION} и 100% при 130 (было 40 и 100); питомцы, турели и другие эффекты, требующие 70%, копируются примерно с 58',
          pl='Krzywa siły mutacji: 70% przy ok. 58 pkt. {@STAT_EVOLUTION} i 100% przy 130 (wcześniej 40 i 100); zwierzaki, wieżyczki i inne efekty wymagające 70% można kopiować od ok. 58',
          es='Curva de potencia de la mutación: 70% con unos 58 de {@STAT_EVOLUTION} y 100% con 130 (antes 40 y 100); mascotas, torretas y otros efectos que requieren 70% se pueden copiar desde unos 58',
          pt='Curva de força da mutação: 70% com cerca de 58 de {@STAT_EVOLUTION} e 100% com 130 (antes 40 e 100); mascotes, torretas e outros efeitos que exigem 70% podem ser copiados a partir de cerca de 58',
          de='Kurve der Mutationsstärke: 70% bei etwa 58 {@STAT_EVOLUTION}, 100% bei 130 (vorher 40 und 100); Haustiere, Geschütze und andere Effekte, die 70% brauchen, sind ab etwa 58 kopierbar',
          tr='Mutasyon gücü eğrisi: yaklaşık 58 {@STAT_EVOLUTION} ile %70, 130 ile %100 (önceden 40 ve 100); %70 güç gerektiren evcil hayvan, taret ve diğer efektler yaklaşık 58\'den itibaren kopyalanabilir',
          it='Curva della potenza della mutazione: 70% a circa 58 di {@STAT_EVOLUTION} e 100% a 130 (prima 40 e 100); animali, torrette e altri effetti che richiedono il 70% si possono copiare da circa 58'),
        N(en='Bosses always evolve when the players\' total {@STAT_EVOLUTION} is above 30 or below −30',
          fr='Les boss évoluent toujours quand la {@STAT_EVOLUTION} totale des joueurs dépasse 30 ou est inférieure à −30',
          zh='玩家的{@STAT_EVOLUTION}总和高于30或低于−30时，头目必定进化',
          ja='プレイヤーの{@STAT_EVOLUTION}合計が30を超えるか−30未満のとき、ボスは必ず進化する',
          ko='플레이어의 {@STAT_EVOLUTION} 합계가 30 초과 또는 −30 미만이면 보스가 반드시 진화함',
          zh_TW='玩家的{@STAT_EVOLUTION}總和高於30或低於−30時，頭目必定進化',
          ru='Боссы всегда эволюционируют, если суммарная {@STAT_EVOLUTION} игроков выше 30 или ниже −30',
          pl='Bossowie zawsze ewoluują, gdy łączna {@STAT_EVOLUTION} graczy przekracza 30 lub jest poniżej −30',
          es='Los jefes siempre evolucionan cuando la {@STAT_EVOLUTION} total de los jugadores supera 30 o es inferior a −30',
          pt='Os chefes sempre evoluem quando a {@STAT_EVOLUTION} total dos jogadores passa de 30 ou fica abaixo de −30',
          de='Bosse entwickeln sich immer, wenn die gesamte {@STAT_EVOLUTION} der Spieler über 30 oder unter −30 liegt',
          tr='Oyuncuların toplam {@STAT_EVOLUTION} değeri 30\'un üstünde veya −30\'un altındaysa bosslar her zaman evrimleşir',
          it="I boss evolvono sempre quando l'{@STAT_EVOLUTION} totale dei giocatori supera 30 o è sotto −30"),
        N(en="Mutation: burn chance effects (e.g. {@ITEM_SCARED_SAUSAGE}) can be copied even when burn chance is already 100%, since each copy still adds damage; the copy's burning damage scales with mutation strength",
          fr="Mutation : les effets de chance de brûlure (ex. {@ITEM_SCARED_SAUSAGE}) peuvent être copiés même à 100 % de chance de brûlure, car chaque copie ajoute des dégâts ; les dégâts de brûlure copiés suivent la puissance de mutation",
          zh="异变：燃烧几率效果（如{@ITEM_SCARED_SAUSAGE}）在燃烧几率已达100%时仍可复制，因为每次复制依然会增加伤害；复制的燃烧伤害随异变强度缩放",
          ja="変異：燃焼確率の効果（{@ITEM_SCARED_SAUSAGE}など）は燃焼確率が100%でもコピーできる（コピーごとにダメージが増えるため）。コピーされた燃焼ダメージは変異の強度に応じて変わる",
          ko="돌연변이: 화상 확률 효과({@ITEM_SCARED_SAUSAGE} 등)는 화상 확률이 이미 100%여도 복제 가능 (복제할 때마다 대미지가 늘어나므로). 복제된 화상 대미지는 돌연변이 강도에 비례",
          zh_TW="異變：燃燒機率效果（如{@ITEM_SCARED_SAUSAGE}）在燃燒機率已達100%時仍可複製，因為每次複製依然會增加傷害；複製的燃燒傷害隨異變強度縮放",
          ru="Мутация: эффекты шанса поджога (напр. {@ITEM_SCARED_SAUSAGE}) копируются даже при 100% шансе поджога, ведь каждая копия добавляет урон; урон горения копии зависит от силы мутации",
          pl="Mutacja: efekty szansy na podpalenie (np. {@ITEM_SCARED_SAUSAGE}) można kopiować nawet przy 100% szansy, bo każda kopia dodaje obrażenia; obrażenia od podpalenia kopii skalują się z siłą mutacji",
          es="Mutación: los efectos de probabilidad de quemadura (p. ej. {@ITEM_SCARED_SAUSAGE}) se pueden copiar aunque la probabilidad ya sea del 100%, pues cada copia añade daño; el daño de quemadura copiado escala con la potencia de la mutación",
          pt="Mutação: efeitos de chance de queimadura (ex.: {@ITEM_SCARED_SAUSAGE}) podem ser copiados mesmo com chance já em 100%, pois cada cópia ainda adiciona dano; o dano de queimadura copiado escala com a força da mutação",
          de="Mutation: Brandchance-Effekte (z. B. {@ITEM_SCARED_SAUSAGE}) können auch bei 100% Brandchance kopiert werden, da jede Kopie weiteren Schaden bringt; der kopierte Brandschaden skaliert mit der Mutationsstärke",
          tr="Mutasyon: yanma şansı efektleri (örn. {@ITEM_SCARED_SAUSAGE}) yanma şansı zaten %100 olsa da kopyalanabilir, çünkü her kopya hasar ekler; kopyanın yanma hasarı mutasyon gücüyle ölçeklenir",
          it="Mutazione: gli effetti di probabilità di ustione (es. {@ITEM_SCARED_SAUSAGE}) si possono copiare anche con probabilità già al 100%, perché ogni copia aggiunge danni; i danni da ustione copiati scalano con la potenza della mutazione"),
        N(en='{@MECA_PARTS_CONSUMABLE}: drop chance per mechanized enemy killed 1.5% → 2.5%',
          fr='{@MECA_PARTS_CONSUMABLE} : chance de butin par ennemi mécanisé tué 1,5 % → 2,5 %',
          zh='{@MECA_PARTS_CONSUMABLE}：每击杀一名机械化敌人的掉落几率 1.5% → 2.5%',
          ja='{@MECA_PARTS_CONSUMABLE}：メカ化した敵1体あたりのドロップ率 1.5% → 2.5%',
          ko='{@MECA_PARTS_CONSUMABLE}: 기계화된 적 처치당 드롭 확률 1.5% → 2.5%',
          zh_TW='{@MECA_PARTS_CONSUMABLE}：每擊殺一名機械化敵人的掉落機率 1.5% → 2.5%',
          ru='{@MECA_PARTS_CONSUMABLE}: шанс выпадения за убитого механизированного врага 1,5% → 2,5%',
          pl='{@MECA_PARTS_CONSUMABLE}: szansa na upuszczenie za zabitego zmechanizowanego wroga 1,5% → 2,5%',
          es='{@MECA_PARTS_CONSUMABLE}: probabilidad de soltarse por enemigo mecanizado eliminado 1,5% → 2,5%',
          pt='{@MECA_PARTS_CONSUMABLE}: chance de queda por inimigo mecanizado abatido 1,5% → 2,5%',
          de='{@MECA_PARTS_CONSUMABLE}: Dropchance pro getötetem mechanisiertem Gegner 1,5% → 2,5%',
          tr='{@MECA_PARTS_CONSUMABLE}: öldürülen her mekanize düşman için düşme şansı %1,5 → %2,5',
          it='{@MECA_PARTS_CONSUMABLE}: probabilità di rilascio per nemico meccanizzato ucciso 1,5% → 2,5%'),
        N(en='Shop: banning a locked item also unlocks it (it used to keep coming back after every reroll)',
          fr='Boutique : bannir un objet verrouillé le déverrouille aussi (il revenait après chaque relance)',
          zh='商店：禁用已锁定的物品时会自动解锁（以前会在之后每次刷新时反复出现）',
          ja='ショップ：ロック中のアイテムを禁止するとロックも解除される（以前はリロールのたびに再登場していた）',
          ko='상점: 잠긴 아이템을 금지하면 잠금도 해제됨 (이전에는 새로고침할 때마다 다시 등장)',
          zh_TW='商店：禁用已鎖定的物品時會自動解鎖（以前會在之後每次刷新時反覆出現）',
          ru='Магазин: запрет заблокированного предмета теперь снимает блокировку (раньше он появлялся после каждого обновления)',
          pl='Sklep: zbanowanie zablokowanego przedmiotu odblokowuje go (wcześniej wracał po każdym odświeżeniu)',
          es='Tienda: vetar un objeto bloqueado también lo desbloquea (antes volvía tras cada renovación)',
          pt='Loja: banir um item travado também o destrava (antes ele voltava a cada atualização)',
          de='Shop: Das Bannen eines gesperrten Gegenstands entsperrt ihn auch (vorher kam er nach jedem Reroll wieder)',
          tr='Mağaza: kilitli bir eşyayı yasaklamak kilidini de açar (önceden her yenilemede geri geliyordu)',
          it='Negozio: bandire un oggetto bloccato lo sblocca anche (prima tornava a ogni rinnovo)'),
        N(en='Shop: when a tier\'s pool runs out, the shop relaxes tag restrictions, then item limits, then the tier; banned items are only a last resort',
          fr='Boutique : quand la réserve d\'un rang est épuisée, la boutique assouplit les étiquettes, puis les limites d\'objets, puis le rang ; les objets bannis ne servent qu\'en dernier recours',
          zh='商店：某一级别的物品池耗尽时，依次放宽标签限制、持有上限和级别限制；已禁用的物品只作为最后的备选',
          ja='ショップ：あるランクのプールが尽きると、タグ制限→所持上限→ランク制限の順に緩和される。禁止アイテムは最後の手段としてのみ出る',
          ko='상점: 한 등급의 풀이 고갈되면 태그 제한, 보유 한도, 등급 제한 순으로 완화됨. 금지한 아이템은 최후의 수단으로만 등장',
          zh_TW='商店：某一級別的物品池耗盡時，依次放寬標籤限制、持有上限和級別限制；已禁用的物品只作為最後的備選',
          ru='Магазин: если пул уровня исчерпан, ослабляются ограничения по тегам, затем лимиты предметов, затем уровень; запрещённые предметы — только в крайнем случае',
          pl='Sklep: gdy pula poziomu się wyczerpie, sklep luzuje ograniczenia tagów, potem limity przedmiotów, potem poziom; zbanowane przedmioty to ostateczność',
          es='Tienda: cuando se agota la reserva de un nivel, se relajan las etiquetas, luego los límites de objetos y luego el nivel; los objetos vetados solo como último recurso',
          pt='Loja: quando o grupo de um nível se esgota, a loja relaxa as etiquetas, depois os limites de itens e depois o nível; itens banidos só como último recurso',
          de='Shop: Ist der Pool einer Stufe erschöpft, werden erst Tag-Beschränkungen, dann Gegenstandslimits, dann die Stufe gelockert; gebannte Gegenstände nur als letzte Option',
          tr='Mağaza: bir seviyenin havuzu bitince sırasıyla etiket kısıtları, eşya limitleri ve seviye gevşetilir; yasaklı eşyalar yalnızca son çare',
          it='Negozio: quando la riserva di un livello si esaurisce, si allentano i vincoli sui tag, poi i limiti degli oggetti, poi il livello; gli oggetti banditi solo come ultima risorsa'),
    ]),
    ('1.2.0.2', [
        N(en='Mutation strength grows faster: 70% at 40 {@STAT_EVOLUTION} (was ~67) and 100% at 100 (was 150)',
          fr='La puissance de la mutation croît plus vite : 70 % à 40 {@STAT_EVOLUTION} (environ 67 avant) et 100 % à 100 (150 avant)',
          zh='异变复制效果的强度提升更快：40点{@STAT_EVOLUTION}时达到70%（原约67点），100点时达到100%（原150点）',
          ja='変異のコピー強度の伸びが速くなった：{@STAT_EVOLUTION}40で70%（以前は約67）、100で100%（以前は150）',
          ko='돌연변이 복제 강도가 더 빠르게 증가: {@STAT_EVOLUTION} 40에서 70% (이전 약 67), 100에서 100% (이전 150)',
          zh_TW='異變複製效果的強度提升更快：40點{@STAT_EVOLUTION}時達到70%（原約67點），100點時達到100%（原150點）',
          ru='Сила мутации растёт быстрее: 70% при 40 ед. {@STAT_EVOLUTION} (было ~67) и 100% при 100 (было 150)',
          pl='Siła mutacji rośnie szybciej: 70% przy 40 pkt. {@STAT_EVOLUTION} (wcześniej ok. 67) i 100% przy 100 (wcześniej 150)',
          es='La potencia de la mutación crece más rápido: 70% con 40 de {@STAT_EVOLUTION} (antes ~67) y 100% con 100 (antes 150)',
          pt='A força da mutação cresce mais rápido: 70% com 40 de {@STAT_EVOLUTION} (antes ~67) e 100% com 100 (antes 150)',
          de='Mutationsstärke wächst schneller: 70% bei 40 {@STAT_EVOLUTION} (vorher ~67), 100% bei 100 (vorher 150)',
          tr='Mutasyon gücü daha hızlı artar: 40 {@STAT_EVOLUTION} ile %70 (önceden ~67), 100 ile %100 (önceden 150)',
          it='La potenza della mutazione cresce più in fretta: 70% a 40 di {@STAT_EVOLUTION} (prima ~67) e 100% a 100 (prima 150)'),
        N(en='From 40 {@STAT_EVOLUTION}, mutation can copy pets, structures and some special effects',
          fr='À partir de 40 {@STAT_EVOLUTION}, la mutation peut copier les familiers, les structures et certains effets spéciaux',
          zh='{@STAT_EVOLUTION}达到40点后，异变可以复制宠物、建筑和部分特殊效果',
          ja='{@STAT_EVOLUTION}40以上で、変異がペット・構造物・一部の特殊効果をコピーできる',
          ko='{@STAT_EVOLUTION} 40부터 돌연변이가 펫, 구조물, 일부 특수 효과를 복제할 수 있음',
          zh_TW='{@STAT_EVOLUTION}達到40點後，異變可以複製寵物、建築和部分特殊效果',
          ru='С 40 ед. {@STAT_EVOLUTION} мутация может копировать питомцев, постройки и некоторые особые эффекты',
          pl='Od 40 pkt. {@STAT_EVOLUTION} mutacja może kopiować zwierzaki, budowle i niektóre efekty specjalne',
          es='Desde 40 de {@STAT_EVOLUTION}, la mutación puede copiar mascotas, estructuras y algunos efectos especiales',
          pt='A partir de 40 de {@STAT_EVOLUTION}, a mutação pode copiar mascotes, estruturas e alguns efeitos especiais',
          de='Ab 40 {@STAT_EVOLUTION} kann die Mutation Haustiere, Bauten und einige Spezialeffekte kopieren',
          tr='40 {@STAT_EVOLUTION} itibarıyla mutasyon evcil hayvanları, yapıları ve bazı özel efektleri kopyalayabilir',
          it='Da 40 di {@STAT_EVOLUTION}, la mutazione può copiare animali, strutture e alcuni effetti speciali'),
        N(en='Mutation no longer copies {@ITEM_ANVIL}; {@ITEM_EXTRA_STOMACH} copied onto {@ITEM_TUMOR} can no longer exceed its per-wave cap',
          fr='La mutation ne copie plus {@ITEM_ANVIL} ; {@ITEM_EXTRA_STOMACH} copié sur {@ITEM_TUMOR} ne peut plus dépasser sa limite par vague',
          zh='异变不再复制{@ITEM_ANVIL}；复制到{@ITEM_TUMOR}上的{@ITEM_EXTRA_STOMACH}不再突破每波上限',
          ja='変異は{@ITEM_ANVIL}をコピーしなくなった。{@ITEM_TUMOR}にコピーされた{@ITEM_EXTRA_STOMACH}はウェーブごとの上限を超えなくなった',
          ko='돌연변이가 더 이상 {@ITEM_ANVIL}을(를) 복제하지 않음. {@ITEM_TUMOR}에 복제된 {@ITEM_EXTRA_STOMACH}은(는) 웨이브당 한도를 넘지 않음',
          zh_TW='異變不再複製{@ITEM_ANVIL}；複製到{@ITEM_TUMOR}上的{@ITEM_EXTRA_STOMACH}不再突破每波上限',
          ru='Мутация больше не копирует {@ITEM_ANVIL}; {@ITEM_EXTRA_STOMACH}, скопированный на {@ITEM_TUMOR}, больше не превышает лимит за волну',
          pl='Mutacja nie kopiuje już {@ITEM_ANVIL}; {@ITEM_EXTRA_STOMACH} skopiowany na {@ITEM_TUMOR} nie przekracza już limitu na falę',
          es='La mutación ya no copia {@ITEM_ANVIL}; {@ITEM_EXTRA_STOMACH} copiado en {@ITEM_TUMOR} ya no supera su límite por oleada',
          pt='A mutação não copia mais {@ITEM_ANVIL}; {@ITEM_EXTRA_STOMACH} copiado no {@ITEM_TUMOR} não ultrapassa mais o limite por onda',
          de='Mutation kopiert {@ITEM_ANVIL} nicht mehr; auf {@ITEM_TUMOR} kopierter {@ITEM_EXTRA_STOMACH} überschreitet nicht mehr das Limit pro Welle',
          tr='Mutasyon artık {@ITEM_ANVIL} kopyalamaz; {@ITEM_TUMOR} üzerine kopyalanan {@ITEM_EXTRA_STOMACH} artık dalga başı sınırı aşamaz',
          it='La mutazione non copia più {@ITEM_ANVIL}; {@ITEM_EXTRA_STOMACH} copiato su {@ITEM_TUMOR} non supera più il limite per ondata'),
        N(en='Effects that do nothing when duplicated or are already capped are no longer copied: {@CHARACTER_SURVIVOR}\'s extra starting weapon choice, {@CHARACTER_TIME_SHIFTER}\'s shuffled waves, {@CHARACTER_CAVEMAN}\'s weapon ignition, material attraction or {@ITEM_TREASURE_MAP} above 100%, {@ITEM_SNAIL} below minimum enemy speed',
          fr='Les effets inutiles une fois dupliqués ou déjà plafonnés ne sont plus copiés : choix d\'arme de départ supplémentaire de {@CHARACTER_SURVIVOR}, vagues mélangées de {@CHARACTER_TIME_SHIFTER}, armes enflammées de {@CHARACTER_CAVEMAN}, attraction des matériaux ou {@ITEM_TREASURE_MAP} au-delà de 100 %, {@ITEM_SNAIL} sous la vitesse minimale des ennemis',
          zh='不再复制重复后无效或已达上限的效果：{@CHARACTER_SURVIVOR}的额外初始武器选择、{@CHARACTER_TIME_SHIFTER}的波次乱序、{@CHARACTER_CAVEMAN}的点燃武器、超过100%的材料吸引和{@ITEM_TREASURE_MAP}、敌人速度已降至下限后的{@ITEM_SNAIL}',
          ja='重複しても意味がない／上限に達した効果はコピーされなくなった：{@CHARACTER_SURVIVOR}の初期武器の追加選択、{@CHARACTER_TIME_SHIFTER}のウェーブ入れ替え、{@CHARACTER_CAVEMAN}の武器点火、100%を超える素材吸引と{@ITEM_TREASURE_MAP}、敵速度が下限に達した後の{@ITEM_SNAIL}',
          ko='중복되면 의미 없거나 이미 한도에 도달한 효과는 더 이상 복제되지 않음: {@CHARACTER_SURVIVOR}의 추가 시작 무기 선택, {@CHARACTER_TIME_SHIFTER}의 웨이브 섞기, {@CHARACTER_CAVEMAN}의 무기 점화, 100%를 넘는 재료 흡수와 {@ITEM_TREASURE_MAP}, 적 속도가 최저치일 때의 {@ITEM_SNAIL}',
          zh_TW='不再複製重複後無效或已達上限的效果：{@CHARACTER_SURVIVOR}的額外初始武器選擇、{@CHARACTER_TIME_SHIFTER}的波次亂序、{@CHARACTER_CAVEMAN}的點燃武器、超過100%的材料吸引和{@ITEM_TREASURE_MAP}、敵人速度已降至下限後的{@ITEM_SNAIL}',
          ru='Больше не копируются эффекты, бесполезные при повторе или уже достигшие предела: доп. выбор стартового оружия {@CHARACTER_SURVIVOR}, перемешанные волны {@CHARACTER_TIME_SHIFTER}, поджог оружия {@CHARACTER_CAVEMAN}, притяжение материалов и {@ITEM_TREASURE_MAP} выше 100%, {@ITEM_SNAIL} при минимальной скорости врагов',
          pl='Nie są już kopiowane efekty bezużyteczne po powieleniu lub osiągnięciu limitu: dodatkowy wybór broni startowej {@CHARACTER_SURVIVOR}, tasowanie fal {@CHARACTER_TIME_SHIFTER}, podpalanie broni {@CHARACTER_CAVEMAN}, przyciąganie materiałów i {@ITEM_TREASURE_MAP} powyżej 100%, {@ITEM_SNAIL} przy minimalnej prędkości wrogów',
          es='Ya no se copian efectos inútiles al duplicarse o ya al máximo: elección extra de arma inicial de {@CHARACTER_SURVIVOR}, oleadas mezcladas de {@CHARACTER_TIME_SHIFTER}, armas encendidas de {@CHARACTER_CAVEMAN}, atracción de materiales y {@ITEM_TREASURE_MAP} por encima del 100%, {@ITEM_SNAIL} con la velocidad enemiga al mínimo',
          pt='Não são mais copiados efeitos inúteis quando duplicados ou já no limite: escolha extra de arma inicial de {@CHARACTER_SURVIVOR}, ondas embaralhadas de {@CHARACTER_TIME_SHIFTER}, armas acesas de {@CHARACTER_CAVEMAN}, atração de materiais e {@ITEM_TREASURE_MAP} acima de 100%, {@ITEM_SNAIL} com a velocidade inimiga no mínimo',
          de='Effekte, die doppelt nutzlos oder schon am Limit sind, werden nicht mehr kopiert: zusätzliche Startwaffenwahl von {@CHARACTER_SURVIVOR}, gemischte Wellen von {@CHARACTER_TIME_SHIFTER}, Waffenentzündung von {@CHARACTER_CAVEMAN}, Materialanziehung und {@ITEM_TREASURE_MAP} über 100%, {@ITEM_SNAIL} bei minimaler Gegnergeschwindigkeit',
          tr='Kopyalanınca işe yaramayan veya sınıra ulaşmış efektler artık kopyalanmaz: {@CHARACTER_SURVIVOR} ek başlangıç silahı seçimi, {@CHARACTER_TIME_SHIFTER} karışık dalgaları, {@CHARACTER_CAVEMAN} silah tutuşturma, %100 üstü malzeme çekme ve {@ITEM_TREASURE_MAP}, düşman hızı en düşükteyken {@ITEM_SNAIL}',
          it='Non vengono più copiati effetti inutili se duplicati o già al massimo: scelta extra dell\'arma iniziale di {@CHARACTER_SURVIVOR}, ondate mescolate di {@CHARACTER_TIME_SHIFTER}, armi accese di {@CHARACTER_CAVEMAN}, attrazione dei materiali e {@ITEM_TREASURE_MAP} oltre il 100%, {@ITEM_SNAIL} con velocità nemica al minimo'),
        N(en='The −1 {@STAT_EVOLUTION} from each mutation now goes to {@ITEM_TUMOR}, which shows the mutation count; an item only becomes mutated when a negative effect is removed from it',
          fr='Le −1 {@STAT_EVOLUTION} de chaque mutation va désormais sur {@ITEM_TUMOR}, qui affiche le nombre de mutations ; un objet ne devient muté que si un effet négatif lui est retiré',
          zh='每次异变的−1{@STAT_EVOLUTION}统一计入{@ITEM_TUMOR}，{@ITEM_TUMOR}会显示累计异变次数；道具只有在被移除负面效果时才会变为异变道具',
          ja='変異ごとの{@STAT_EVOLUTION}−1は{@ITEM_TUMOR}に計上され、{@ITEM_TUMOR}に変異回数が表示される。アイテムはマイナス効果が除去された時だけ変異アイテムになる',
          ko='돌연변이마다의 {@STAT_EVOLUTION} −1은 이제 {@ITEM_TUMOR}에 합산되며 돌연변이 횟수가 표시됨. 아이템은 부정적 효과가 제거될 때만 돌연변이 아이템이 됨',
          zh_TW='每次異變的−1{@STAT_EVOLUTION}統一計入{@ITEM_TUMOR}，{@ITEM_TUMOR}會顯示累計異變次數；道具只有在被移除負面效果時才會變為異變道具',
          ru='−1 {@STAT_EVOLUTION} за каждую мутацию теперь идёт на {@ITEM_TUMOR}, где показывается число мутаций; предмет становится мутировавшим, только если с него снят негативный эффект',
          pl='−1 pkt. {@STAT_EVOLUTION} z każdej mutacji trafia teraz na {@ITEM_TUMOR}, który pokazuje liczbę mutacji; przedmiot staje się zmutowany tylko po usunięciu negatywnego efektu',
          es='El −1 de {@STAT_EVOLUTION} de cada mutación va ahora a {@ITEM_TUMOR}, que muestra el número de mutaciones; un objeto solo queda mutado cuando se le quita un efecto negativo',
          pt='O −1 de {@STAT_EVOLUTION} de cada mutação agora vai para o {@ITEM_TUMOR}, que mostra a contagem de mutações; um item só fica mutado quando um efeito negativo é removido dele',
          de='Die −1 {@STAT_EVOLUTION} jeder Mutation geht jetzt auf {@ITEM_TUMOR}, der die Anzahl der Mutationen zeigt; ein Gegenstand wird nur mutiert, wenn ihm ein negativer Effekt entfernt wird',
          tr='Her mutasyonun −1 {@STAT_EVOLUTION} değeri artık {@ITEM_TUMOR} üzerinde toplanır ve mutasyon sayısını gösterir; bir eşya yalnızca negatif efekti kaldırıldığında mutasyonlu olur',
          it='Il −1 di {@STAT_EVOLUTION} di ogni mutazione ora va su {@ITEM_TUMOR}, che mostra il numero di mutazioni; un oggetto diventa mutato solo quando gli viene rimosso un effetto negativo'),
        N(en='Copied explosion chances are rounded up to a whole percent',
          fr='Les chances d\'explosion copiées sont arrondies au pourcent supérieur',
          zh='复制的爆炸几率向上取整到整数百分比',
          ja='コピーされた爆発確率は整数％に切り上げられる',
          ko='복제된 폭발 확률은 정수 %로 올림됨',
          zh_TW='複製的爆炸機率向上取整到整數百分比',
          ru='Скопированный шанс взрыва округляется вверх до целого процента',
          pl='Skopiowana szansa na wybuch jest zaokrąglana w górę do pełnego procentu',
          es='La probabilidad de explosión copiada se redondea hacia arriba a un porcentaje entero',
          pt='A chance de explosão copiada é arredondada para cima até um percentual inteiro',
          de='Kopierte Explosionschancen werden auf ganze Prozent aufgerundet',
          tr='Kopyalanan patlama şansı tam yüzdeye yukarı yuvarlanır',
          it='Le probabilità di esplosione copiate sono arrotondate per eccesso al punto percentuale'),
        N(en='{@MUTATION_CONSUMABLE_FRUIT}: base drop chance 3% → 4%; from wave 30 it drops by 1% every 10 waves (min 1%)',
          fr='{@MUTATION_CONSUMABLE_FRUIT} : chance de butin de base 3 % → 4 % ; dès la vague 30, −1 % toutes les 10 vagues (min. 1 %)',
          zh='{@MUTATION_CONSUMABLE_FRUIT}：基础掉落几率 3% → 4%；从第30波起每10波降低1%，最低1%',
          ja='{@MUTATION_CONSUMABLE_FRUIT}：基本ドロップ率 3% → 4%。ウェーブ30以降は10ウェーブごとに1%低下（最低1%）',
          ko='{@MUTATION_CONSUMABLE_FRUIT}: 기본 드롭 확률 3% → 4%. 30웨이브부터 10웨이브마다 1% 감소 (최소 1%)',
          zh_TW='{@MUTATION_CONSUMABLE_FRUIT}：基礎掉落機率 3% → 4%；從第30波起每10波降低1%，最低1%',
          ru='{@MUTATION_CONSUMABLE_FRUIT}: базовый шанс выпадения 3% → 4%; с 30-й волны −1% каждые 10 волн (мин. 1%)',
          pl='{@MUTATION_CONSUMABLE_FRUIT}: bazowa szansa na upuszczenie 3% → 4%; od 30. fali spada o 1% co 10 fal (min. 1%)',
          es='{@MUTATION_CONSUMABLE_FRUIT}: probabilidad base 3% → 4%; desde la oleada 30 baja un 1% cada 10 oleadas (mín. 1%)',
          pt='{@MUTATION_CONSUMABLE_FRUIT}: chance base 3% → 4%; a partir da onda 30 cai 1% a cada 10 ondas (mín. 1%)',
          de='{@MUTATION_CONSUMABLE_FRUIT}: Basis-Dropchance 3% → 4%; ab Welle 30 alle 10 Wellen −1% (min. 1%)',
          tr='{@MUTATION_CONSUMABLE_FRUIT}: temel düşme şansı %3 → %4; 30. dalgadan itibaren her 10 dalgada %1 azalır (en az %1)',
          it='{@MUTATION_CONSUMABLE_FRUIT}: probabilità base 3% → 4%; dall\'ondata 30 cala dell\'1% ogni 10 ondate (min. 1%)'),
        N(en='{@MECA_PARTS_CONSUMABLE}: drop chance 2% → 1.5%',
          fr='{@MECA_PARTS_CONSUMABLE} : chance de butin 2 % → 1,5 %',
          zh='{@MECA_PARTS_CONSUMABLE}：掉落几率 2% → 1.5%',
          ja='{@MECA_PARTS_CONSUMABLE}：ドロップ率 2% → 1.5%',
          ko='{@MECA_PARTS_CONSUMABLE}: 드롭 확률 2% → 1.5%',
          zh_TW='{@MECA_PARTS_CONSUMABLE}：掉落機率 2% → 1.5%',
          ru='{@MECA_PARTS_CONSUMABLE}: шанс выпадения 2% → 1,5%',
          pl='{@MECA_PARTS_CONSUMABLE}: szansa na upuszczenie 2% → 1,5%',
          es='{@MECA_PARTS_CONSUMABLE}: probabilidad 2% → 1,5%',
          pt='{@MECA_PARTS_CONSUMABLE}: chance de queda 2% → 1,5%',
          de='{@MECA_PARTS_CONSUMABLE}: Dropchance 2% → 1,5%',
          tr='{@MECA_PARTS_CONSUMABLE}: düşme şansı %2 → %1,5',
          it='{@MECA_PARTS_CONSUMABLE}: probabilità di rilascio 2% → 1,5%'),
        N(en='Mechanizing a weapon: damage bonus per mecha power 5% → 3% (8 times: +180% → +108%), and no extra piercing or bounce anymore',
          fr='Mécanisation d\'arme : bonus de dégâts par puissance méca 5 % → 3 % (8 fois : +180 % → +108 %), plus de perforation ni de rebond supplémentaires',
          zh='武器机械化：每点机械强度的伤害加成 5% → 3%（机械化8次时 +180% → +108%），不再额外提供穿透或弹射',
          ja='武器のメカ化：メカパワー1あたりのダメージボーナス 5% → 3%（8回で+180% → +108%）。追加の貫通・跳弾はなくなった',
          ko='무기 기계화: 기계 파워당 대미지 보너스 5% → 3% (8회 시 +180% → +108%), 추가 관통·튕김 없음',
          zh_TW='武器機械化：每點機械強度的傷害加成 5% → 3%（機械化8次時 +180% → +108%），不再額外提供穿透或彈射',
          ru='Механизация оружия: бонус урона за единицу мощности 5% → 3% (8 раз: +180% → +108%), больше нет доп. пробивания и рикошета',
          pl='Mechanizacja broni: premia do obrażeń za punkt mocy mecha 5% → 3% (8 razy: +180% → +108%), bez dodatkowego przebicia i odbicia',
          es='Mecanizar armas: bonificación de daño por poder meca 5% → 3% (8 veces: +180% → +108%), ya sin perforación ni rebote extra',
          pt='Mecanizar armas: bônus de dano por poder meca 5% → 3% (8 vezes: +180% → +108%), sem perfuração ou ricochete extra',
          de='Waffe mechanisieren: Schadensbonus pro Mecha-Kraft 5% → 3% (8-mal: +180% → +108%), kein zusätzlicher Durchschlag oder Abpraller mehr',
          tr='Silah mekanizasyonu: mekanik güç başına hasar bonusu %5 → %3 (8 kez: +%180 → +%108), artık ek delme veya sekme yok',
          it='Meccanizzare un\'arma: bonus danni per potenza meca 5% → 3% (8 volte: +180% → +108%), niente più perforazione o rimbalzo extra'),
        N(en='Mechanizing a weapon: stat options are lower; they reach the tier IV values at level 8 (was 4) and stop growing after that, while the cost keeps rising',
          fr='Mécanisation d\'arme : options de stats réduites ; elles atteignent les valeurs du rang IV au niveau 8 (4 avant) puis cessent de croître, le coût continue d\'augmenter',
          zh='武器机械化：可选属性数值下调，强化到8级时才达到IV级品质的数值（原为4级），之后不再增长；费用仍会继续增加',
          ja='武器のメカ化：選べるステータスの値が低下。強化レベル8でランクIVの値に達し（以前は4）、以降は伸びない。費用は上がり続ける',
          ko='무기 기계화: 선택 능력치 수치 하향. 강화 8레벨에서 IV 등급 수치에 도달(이전 4레벨)하고 이후 증가하지 않음. 비용은 계속 증가',
          zh_TW='武器機械化：可選屬性數值下調，強化到8級時才達到IV級品質的數值（原為4級），之後不再增長；費用仍會繼續增加',
          ru='Механизация оружия: значения характеристик снижены; они достигают значений уровня IV на 8-м уровне (было 4) и дальше не растут, а цена продолжает расти',
          pl='Mechanizacja broni: niższe opcje statystyk; osiągają wartości poziomu IV na 8. poziomie (wcześniej 4) i potem nie rosną, a koszt nadal rośnie',
          es='Mecanizar armas: opciones de estadísticas más bajas; alcanzan los valores de nivel IV en el nivel 8 (antes 4) y dejan de crecer, mientras el coste sigue subiendo',
          pt='Mecanizar armas: opções de atributos menores; atingem os valores de nível IV no nível 8 (antes 4) e param de crescer, enquanto o custo continua subindo',
          de='Waffe mechanisieren: niedrigere Werteoptionen; sie erreichen auf Stufe 8 (vorher 4) die Werte von Stufe IV und wachsen danach nicht weiter, die Kosten steigen weiter',
          tr='Silah mekanizasyonu: stat seçenekleri düşürüldü; IV. seviye değerlerine 8. seviyede (önceden 4) ulaşır ve sonra artmaz, maliyet artmaya devam eder',
          it='Meccanizzare un\'arma: opzioni statistiche più basse; raggiungono i valori di livello IV al livello 8 (prima 4) e poi non crescono più, mentre il costo continua a salire'),
        N(en='Ban: you get 1 ban token every 4 waves, up to wave 20',
          fr='Bannissement : 1 jeton de bannissement toutes les 4 vagues, jusqu\'à la vague 20',
          zh='禁用：每经过4波获得1枚禁用代币，直到第20波',
          ja='禁止：4ウェーブごとに禁止トークンを1枚獲得（ウェーブ20まで）',
          ko='금지: 4웨이브마다 금지 토큰 1개 획득 (20웨이브까지)',
          zh_TW='禁用：每經過4波獲得1枚禁用代幣，直到第20波',
          ru='Запрет: 1 жетон запрета каждые 4 волны, до 20-й волны',
          pl='Banowanie: 1 żeton bana co 4 fale, do 20. fali',
          es='Veto: 1 ficha de veto cada 4 oleadas, hasta la oleada 20',
          pt='Banimento: 1 ficha de banimento a cada 4 ondas, até a onda 20',
          de='Bannen: alle 4 Wellen 1 Bann-Marke, bis Welle 20',
          tr='Yasaklama: dalga 20\'ye kadar her 4 dalgada 1 yasak jetonu',
          it='Bando: 1 gettone di bando ogni 4 ondate, fino all\'ondata 20'),
    ]),
    ('1.2.0.1', [
        N(en='{@MUTATION_CONSUMABLE_FRUIT}: base drop chance from mutated enemies 2% → 3%',
          fr='{@MUTATION_CONSUMABLE_FRUIT} : chance de butin de base des ennemis mutés 2 % → 3 %',
          zh='{@MUTATION_CONSUMABLE_FRUIT}：异变敌人的基础掉落几率 2% → 3%',
          ja='{@MUTATION_CONSUMABLE_FRUIT}：変異した敵からの基本ドロップ率 2% → 3%',
          ko='{@MUTATION_CONSUMABLE_FRUIT}: 돌연변이 적의 기본 드롭 확률 2% → 3%',
          zh_TW='{@MUTATION_CONSUMABLE_FRUIT}：異變敵人的基礎掉落機率 2% → 3%',
          ru='{@MUTATION_CONSUMABLE_FRUIT}: базовый шанс выпадения с мутировавших врагов 2% → 3%',
          pl='{@MUTATION_CONSUMABLE_FRUIT}: bazowa szansa na upuszczenie przez zmutowanych wrogów 2% → 3%',
          es='{@MUTATION_CONSUMABLE_FRUIT}: probabilidad base en enemigos mutados 2% → 3%',
          pt='{@MUTATION_CONSUMABLE_FRUIT}: chance base em inimigos mutados 2% → 3%',
          de='{@MUTATION_CONSUMABLE_FRUIT}: Basis-Dropchance mutierter Gegner 2% → 3%',
          tr='{@MUTATION_CONSUMABLE_FRUIT}: mutasyonlu düşmanlardan temel düşme şansı %2 → %3',
          it='{@MUTATION_CONSUMABLE_FRUIT}: probabilità base dai nemici mutati 2% → 3%'),
        N(en='Mutation can no longer copy {@CHARACTER_SURVIVOR}\'s "no weapons in the shop"',
          fr='La mutation ne peut plus copier « pas d\'armes en boutique » de {@CHARACTER_SURVIVOR}',
          zh='异变不再能复制{@CHARACTER_SURVIVOR}的“商店里没有武器”',
          ja='変異は{@CHARACTER_SURVIVOR}の「ショップに武器が出ない」をコピーできなくなった',
          ko='돌연변이가 더 이상 {@CHARACTER_SURVIVOR}의 "상점에 무기 없음"을 복제할 수 없음',
          zh_TW='異變不再能複製{@CHARACTER_SURVIVOR}的「商店裡沒有武器」',
          ru='Мутация больше не копирует «нет оружия в магазине» {@CHARACTER_SURVIVOR}',
          pl='Mutacja nie kopiuje już „brak broni w sklepie” postaci {@CHARACTER_SURVIVOR}',
          es='La mutación ya no puede copiar «no hay armas en la tienda» de {@CHARACTER_SURVIVOR}',
          pt='A mutação não pode mais copiar "sem armas na loja" de {@CHARACTER_SURVIVOR}',
          de='Mutation kann „keine Waffen im Shop“ von {@CHARACTER_SURVIVOR} nicht mehr kopieren',
          tr='Mutasyon artık {@CHARACTER_SURVIVOR} karakterinin "mağazada silah yok" efektini kopyalayamaz',
          it='La mutazione non può più copiare «nessuna arma nel negozio» di {@CHARACTER_SURVIVOR}'),
    ]),
    ('1.2.0.0', [
        N(en='Shop: weapons you own appear more often: 20% → 23%, early-wave bonus 5% → 7%, plus 2% per different weapon owned (up to 6)',
          fr='Boutique : les armes possédées apparaissent plus souvent : 20 % → 23 %, bonus des premières vagues 5 % → 7 %, +2 % par arme différente possédée (jusqu\'à 6)',
          zh='商店：已持有武器的出现几率 20% → 23%，前期波次额外加成 5% → 7%；每持有一种不同武器再 +2%（最多计6种）',
          ja='ショップ：所持武器の出現率 20% → 23%、序盤ウェーブのボーナス 5% → 7%。異なる武器1種につき+2%（最大6種）',
          ko='상점: 보유한 무기 등장 확률 20% → 23%, 초반 웨이브 보너스 5% → 7%, 서로 다른 무기 1종당 +2% (최대 6종)',
          zh_TW='商店：已持有武器的出現機率 20% → 23%，前期波次額外加成 5% → 7%；每持有一種不同武器再 +2%（最多計6種）',
          ru='Магазин: имеющееся оружие появляется чаще: 20% → 23%, бонус ранних волн 5% → 7%, +2% за каждое разное оружие (до 6)',
          pl='Sklep: posiadane bronie pojawiają się częściej: 20% → 23%, premia we wczesnych falach 5% → 7%, +2% za każdą inną posiadaną broń (do 6)',
          es='Tienda: las armas que tienes aparecen más: 20% → 23%, bonificación de oleadas tempranas 5% → 7%, +2% por cada arma distinta (hasta 6)',
          pt='Loja: armas que você tem aparecem mais: 20% → 23%, bônus das primeiras ondas 5% → 7%, +2% por arma diferente (até 6)',
          de='Shop: Waffen im Besitz erscheinen öfter: 20% → 23%, Bonus früher Wellen 5% → 7%, +2% pro unterschiedlicher Waffe (bis 6)',
          tr='Mağaza: sahip olunan silahlar daha sık çıkar: %20 → %23, erken dalga bonusu %5 → %7, her farklı silah için +%2 (en fazla 6)',
          it='Negozio: le armi possedute compaiono più spesso: 20% → 23%, bonus delle prime ondate 5% → 7%, +2% per ogni arma diversa (fino a 6)'),
        N(en='Shop: weapons of the same class as yours appear 1% more often per different weapon owned (up to 6)',
          fr='Boutique : les armes de la même classe que les vôtres apparaissent 1 % plus souvent par arme différente possédée (jusqu\'à 6)',
          zh='商店：每持有一种不同武器，其所属类别武器的出现几率 +1%（最多计6种）',
          ja='ショップ：異なる武器1種につき、その種類の武器の出現率+1%（最大6種）',
          ko='상점: 서로 다른 무기 1종당 해당 분류 무기의 등장 확률 +1% (최대 6종)',
          zh_TW='商店：每持有一種不同武器，其所屬類別武器的出現機率 +1%（最多計6種）',
          ru='Магазин: оружие того же класса появляется на 1% чаще за каждое разное оружие (до 6)',
          pl='Sklep: bronie tej samej klasy pojawiają się o 1% częściej za każdą inną posiadaną broń (do 6)',
          es='Tienda: las armas de la misma clase aparecen un 1% más por cada arma distinta (hasta 6)',
          pt='Loja: armas da mesma classe aparecem 1% mais por arma diferente (até 6)',
          de='Shop: Waffen derselben Klasse erscheinen pro unterschiedlicher Waffe 1% öfter (bis 6)',
          tr='Mağaza: her farklı silah için aynı sınıftaki silahlar %1 daha sık çıkar (en fazla 6)',
          it='Negozio: le armi della stessa classe compaiono l\'1% più spesso per ogni arma diversa (fino a 6)'),
    ]),
]


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------
_snap_cache = {}


def _load_snap(ref, lang):
    k = (ref, lang)
    if k not in _snap_cache:
        raw = subprocess.check_output(['git', 'show', f'{ref}:public/data/brotato_data.{lang}.json'], cwd=CODEX_DIR)
        d = json.loads(raw.decode('utf-8'))
        _snap_cache[k] = {cat: {e['id']: e for e in d[cat]} for cat in ('weapons', 'items', 'characters')}
    return _snap_cache[k]


def _fmt(v, dp=None):
    if dp is not None:
        return ('%.*f' % (dp, float(v))).rstrip('0').rstrip('.')
    f = float(v)
    return str(int(f + 0.5) if f >= 0 else -int(-f + 0.5))   # JS Math.round


def _fill(tmpl, args):
    args = args or []

    def rep(m):
        i = int(m.group(1))
        a = args[i] if i < len(args) else None
        if not a:
            return m.group(0)
        if a.get('type') == 'linked':
            base = args[0]['value'] if args and args[0] else 0
            return _fmt(round(base) * a.get('linked_mult', 1), a.get('decimalPlaces'))
        if a.get('type') == 'random' and a.get('curse_min') is None:
            pass
        return _fmt(a['value'], a.get('decimalPlaces'))
    return re.sub(r'\{(\d+)\}', rep, tmpl or '')


def _plain(html):
    return re.sub(r'<[^>]+>', '', html or '')


class _Ctx:
    def __init__(self, data, tr, render):
        self.tr, self.render = tr, render
        self.cur = {cat: {e['id']: e for e in data[cat]} for cat in ('weapons', 'items', 'characters')}

    # {lang: filled text} for an effect of the data being built (text dict has all langs)
    def cur_eff(self, eff):
        t = eff.get('text') or {}
        return {L: _fill(t.get(L) or t.get('en', ''), t.get('args')) for L in LANGS}

    def render_eff(self, eff, parent_id, is_weapon):
        out = {}
        for L in LANGS:
            t, a = self.render(copy.deepcopy(eff), L, parent_id, is_weapon)
            out[L] = _fill(t, a)
        return out

    def snap_effs(self, ref, cat, eid):
        """[{lang: text}] for the effects of an entry in snapshot `ref` (or 'cur')."""
        if ref == 'cur':
            e = self.cur[cat].get(eid)
            return None if e is None else [self.cur_eff(x) for x in e.get('effects', [])]
        per_lang = {L: _load_snap(ref, L)[cat].get(eid) for L in LANGS}
        if per_lang['en'] is None:
            return None
        n = len(per_lang['en'].get('effects', []))
        out = []
        for i in range(n):
            d = {}
            for L in LANGS:
                x = per_lang[L]['effects'][i]
                t = x.get('text') or {}
                d[L] = _fill(t.get(L, ''), t.get('args'))
            out.append(d)
        return out

    def snap_entry(self, ref, cat, eid):
        if ref == 'cur':
            return self.cur[cat].get(eid)
        return _load_snap(ref, 'en')[cat].get(eid)

    def name(self, eid):
        for cat in ('weapons', 'items', 'characters'):
            e = self.cur[cat].get(eid)
            if e:
                return {L: e.get(f'name_{L}') or e.get('name_en') or eid for L in LANGS}
        return {L: eid for L in LANGS}

    def subst(self, text, L):
        return re.sub(r'\{@([A-Z0-9_]+)\}', lambda m: self.tr(m.group(1), L), text)


def _nums(html):
    return re.findall(r'\d+(?:\.\d+)?', _cmp_text(html))


def _cmp_text(html):
    """Text for comparison: markup removed except scaling tags, without their curse-only fixed="1"."""
    return re.sub(r'<(?!scaling)[^>]+>', '', html or '').replace(' fixed="1"', '')


def _join(vals):
    """Per-tier values; one value when every tier is the same."""
    return vals[0] if len(set(vals)) == 1 else ' / '.join(vals)


def _diff_effects(old, new):
    """Align two effect-text lists ([{lang: text}]) -> [line]."""
    key = lambda d: _cmp_text(d['en'])   # keeps scaling values
    sm = difflib.SequenceMatcher(a=[key(x) for x in old], b=[key(x) for x in new], autojunk=False)
    lines = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            continue
        a, b = old[i1:i2], new[j1:j2]
        for k in range(max(len(a), len(b))):
            if k < len(a) and k < len(b):
                if _nums(a[k]['en']) != _nums(b[k]['en']):   # same numbers = rewording only
                    lines.append({'k': 'chg', 'from': a[k], 'to': b[k]})
            elif k < len(a):
                lines.append({'k': 'del', 'text': a[k]})
            else:
                lines.append({'k': 'add', 'text': b[k]})
    return lines


# weapon stat fields: (stats key, ui label key, formatter)
_PCT = lambda v: _fmt(v * 100) + '%'
_WEAPON_STATS = [
    ('damage', 'damage', _fmt),
    ('crit_chance', 'crit', _PCT),
    ('crit_damage', 'crit', lambda v: '×' + _fmt(v, 2)),
    ('cooldown', 'cooldown', lambda v: _fmt(v / 60, 2) + 's'),
    ('knockback', 'knockback', _fmt),
    ('max_range', 'range', _fmt),
    ('accuracy', 'accuracy', _PCT),
    ('lifesteal', 'lifesteal', _PCT),
    ('piercing', 'piercing', _fmt),
    ('bounce', 'bounce', _fmt),
    ('nb_projectiles', 'projectiles', _fmt),
]


def _tiers_label(tiers, all_tiers):
    if len(all_tiers) <= 1 or tiers == all_tiers:
        return ''
    return ' / '.join(ROMAN[t] for t in tiers)


def _weapon_family(ctx, ref, fam):
    src = ctx.cur['weapons'] if ref == 'cur' else _load_snap(ref, 'en')['weapons']
    return {e['tier']: e for e in src.values() if e.get('weapon_id') == fam}


def _snap_weapon(ctx, old_ref, new_ref, fam):
    old_t, new_t = _weapon_family(ctx, old_ref, fam), _weapon_family(ctx, new_ref, fam)
    lines = []
    removed = sorted(set(old_t) - set(new_t))
    if removed:
        lines.append({'k': 'tier_del', 'list': ' / '.join(ROMAN[t] for t in removed)})
    common = sorted(set(old_t) & set(new_t))
    if common:   # weapon classes (all tiers share them)
        sa, sb = old_t[common[0]].get('sets') or [], new_t[common[0]].get('sets') or []
        if sa != sb:
            cls = lambda ks: {L: ', '.join(ctx.tr(k, L) for k in ks) for L in LANGS}
            lines.append({'k': 'stat', 'label': 'set', 'from': cls(sa), 'to': cls(sb)})
    for key, label, f in _WEAPON_STATS:
        ov = [old_t[t]['stats'].get(key) for t in common]
        nv = [new_t[t]['stats'].get(key) for t in common]
        if ov != nv and None not in ov + nv:
            lines.append({'k': 'stat', 'label': label, 'from': _join([f(v) for v in ov]),
                          'to': _join([f(v) for v in nv])})
    # scaling stats: one line, all stats of a tier together
    tags = lambda e: ''.join(f'<scaling type="{k[5:]}" value="{v}" />' for k, v in e['stats'].get('scaling_stats', []))
    ov, nv = [tags(old_t[t]) for t in common], [tags(new_t[t]) for t in common]
    if ov != nv:
        lines.append({'k': 'stat', 'label': '', 'from': _join(ov), 'to': _join(nv)})
    # effects, grouped by identical change across tiers
    groups = {}
    for t in common:
        o = ctx.snap_effs(old_ref, 'weapons', old_t[t]['id']) or []
        n = ctx.snap_effs(new_ref, 'weapons', new_t[t]['id']) or []
        for ln in _diff_effects(o, n):
            k = json.dumps(ln, ensure_ascii=False, sort_keys=True)
            groups.setdefault(k, (ln, []))[1].append(t)
    for ln, ts in groups.values():
        lab = _tiers_label(ts, common)
        if lab:
            ln['tiers'] = lab
        lines.append(ln)
    return lines


def _set_dotted(d, path, v):
    ks = path.split('.')
    for k in ks[:-1]:
        d = d.setdefault(k, {})
    d[ks[-1]] = v


def _get_dotted(d, path):
    for k in path.split('.'):
        d = (d or {}).get(k)
    return d


def _find_eff(entry, match):
    for e in entry.get('effects', []):
        if match in (e.get('key'), e.get('text_key')):
            return e
    raise KeyError(f"{entry['id']}: no effect {match}")


def _entry_lines(ctx, eid, ops):
    is_weapon = eid.startswith('weapon_') and eid not in ctx.cur['weapons']
    cat = 'weapons' if is_weapon else ('characters' if eid.startswith('character_') else 'items')
    entry = None if is_weapon else ctx.cur[cat].get(eid)
    if not is_weapon and entry is None:
        raise KeyError(f'history: unknown entry {eid}')
    lines = []
    for op in ops:
        kind = op[0]
        if kind == 'snap':
            _, a, b = op
            if is_weapon:
                lines += _snap_weapon(ctx, a, b, eid)
                continue
            lines += _diff_effects(ctx.snap_effs(a, cat, eid) or [], ctx.snap_effs(b, cat, eid) or [])
            ea, eb = ctx.snap_entry(a, cat, eid), ctx.snap_entry(b, cat, eid)
            if ea and eb and ea.get('value') != eb.get('value'):
                lines.append({'k': 'stat', 'label': 'price', 'from': _fmt(ea.get('value')),
                              'to': _fmt(eb.get('value'))})
            if ea and eb and ea.get('max_nb') != eb.get('max_nb'):
                lines.append({'k': 'stat', 'label': 'histMaxNb', 'from': _fmt(ea.get('max_nb')),
                              'to': _fmt(eb.get('max_nb'))})
        elif kind == 'eff':
            _, match, old = op
            cur = _find_eff(entry, match)
            pid, isw = cur.get('_parent_id', eid), cur.get('_is_weapon', False)
            base = {k: v for k, v in cur.items() if k not in ('text', 'mut_args', 'icon')}
            olde = copy.deepcopy(base)
            for k, v in old.items():
                _set_dotted(olde, k, v)
            t_old, t_new = ctx.render_eff(olde, pid, isw), ctx.cur_eff(cur)
            if _plain(t_old['en']) != _plain(t_new['en']):
                lines.append({'k': 'chg', 'from': t_old, 'to': t_new})
            else:   # value not shown in the text
                k0 = next(iter(old))
                lines.append({'k': 'stat', 'label_text': t_new, 'from': _fmt(old[k0]),
                              'to': _fmt(_get_dotted(base, k0))})
        elif kind == 'add_eff':
            lines.append({'k': 'add', 'text': ctx.cur_eff(_find_eff(entry, op[1]))})
        elif kind == 'del_eff':
            lines.append({'k': 'del', 'text': ctx.render_eff(op[1], eid, False)})
        elif kind == 'start':
            _, add, rem = op
            lines.append({'k': 'start', 'add': [ctx.name(x) for x in add], 'del': [ctx.name(x) for x in rem]})
        elif kind == 'ban':
            lines.append({'k': 'ban', 'add': [ctx.name(x) for x in op[1]]})
        elif kind == 'no_upgrade':
            lines.append({'k': 'no_upgrade', 'stat': {L: ctx.tr(op[1].upper(), L) for L in LANGS}})
        elif kind == 'start_for':
            lines.append({'k': 'start_for', 'names': [ctx.name(x) for x in op[1]]})
        elif kind == 'new':
            lines.append({'k': 'new'})
        elif kind == 'note':
            lines.append({'k': 'note', 'text': {L: ctx.subst(op[1][L], L) for L in LANGS}})
        else:
            raise ValueError(kind)
    if not lines:
        raise ValueError(f'history: {eid} {ops} produced no lines')
    return lines


def _vkey(v):
    return [int(x) for x in re.findall(r'\d+', v)]


def build_history(data, tr, render):
    """-> (entry_history {id: [{v, lines}]}, mech_history [{v, lines}]); texts are {lang: str}."""
    ctx = _Ctx(data, tr, render)
    hist = {}
    for v, eid, ops in ENTRY_HISTORY:
        lst = hist.setdefault(eid, [])
        same = next((x for x in lst if x['v'] == v), None)
        if same:
            same['lines'] += _entry_lines(ctx, eid, ops)
        else:
            lst.append({'v': v, 'lines': _entry_lines(ctx, eid, ops)})
    for lst in hist.values():
        lst.sort(key=lambda x: _vkey(x['v']), reverse=True)
    mech = [{'v': v, 'lines': [{'k': 'note', 'text': {L: ctx.subst(n[L], L) for L in LANGS}} for n in notes]}
            for v, notes in MECH_HISTORY]
    mech.sort(key=lambda x: _vkey(x['v']), reverse=True)
    return hist, mech


def prune_lang(obj, L):
    """Replace every {lang: text} dict with its text for L."""
    if isinstance(obj, dict):
        if 'en' in obj and set(obj) <= set(LANGS):
            return obj.get(L) or obj['en']
        return {k: prune_lang(v, L) for k, v in obj.items()}
    if isinstance(obj, list):
        return [prune_lang(x, L) for x in obj]
    return obj
