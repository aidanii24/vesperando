import json
import sys
import os


def export_battle_book_extras():
    content: dict[int, str] = {
        860150: "vesperando: Target Types 1",
        860151: "[Enemy Target]\n"
                "Arte is focused for one enemy, but can still catch strays\n"
                "[All Enemies]\n"
                "All enemies will be affected by arte regardless of range\n"
                "[Area of Effect]\n"
                "Freely damages enemies and buffs allies within range",
        860152: "vesperando: Target Types 2",
        860153: "[Single Ally]\n"
                "Arte is focused for one ally, but may still affect \n"
                "other allies or damage enemies if close enough\n"
                "[All Allies]\n"
                "All allies will be affected by arte regardless of range\n"
                "[Allies Only]\n"
                "Arte will target allies, \n"
                "ignoring any enemy along the way\n"
                "[Self]\n"
                "Arte will only affect the user",
        860154: "vesperando: Global Effects 1",
        860155: "\u2665\x06(FS1) HP Recovery\n"
                "\x06(SC6)\x06(FS1) KO Recovery\n"
                "\x06(ST4)\x06(FS3) Cure Physical Ailments\n"
                "\x06(SC7)\x06(FS3) Cure Magical Ailments\n"
                "\x06(SC1)\x06(FS1) Physical Attack Up\n"
                "\x06(SC3)\x06(FS1) Magical Attack Up\n"
                "\x06(SC2)\x06(FS1) Physical Defense Up\n"
                "\x06(SC4)\x06(FS1) Magical Defense Up",
        860156: "vesperando: Global Effects 2",
        860157: "\x06(SC6)\x06(FS2) Auto-recover\n"
                "\x06(SC2)\x06(FS2) Iron Stance\n"
                "\x06(SC4)\x06(FS2) Invulnerability\n"
                "\x06(EL5)\x06(FS2) Imbue Element\n"
                "\x06(EL7)\x06(FS1) TP Recovery\n"
                "\x06(EL7)\x06(FS2) Reduce Damage\n"
                "\x06(SC3)\x06(FS2) Luck Up",
    }

    btlb: dict[int, int] = {
        860150: 860151,
        860152: 860153,
        860154: 860155,
        860156: 860157,
    }

    data: dict = {
        'strings': content,
        'pairs': {
            'btlb': btlb
        }
    }

    filepath: str = "scripts/artifacts/strings.json"
    os.makedirs("./artifacts", exist_ok=True)
    with open(filepath, "w+") as f:
        json.dump(data, f)
        f.flush()
        f.close()


if "__main__" == __name__:
    match sys.argv[1]:
        case 'BTLB':
            export_battle_book_extras()
        case _:
            print(
                "vesperando: string.py"
                "\nvesperando string data utiliy"
                "\n\n"
                "Subcommands:"
                f"\n{"BTLB":<18}Export extra Battle Book strings as JSON to artifacts/"
            )