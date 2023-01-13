from ass_parser import AssFile

# clip pathing
clipa = r"\iclip(m 939.69 325.05 b 936.23 359.79 926.13 428.53 918.86 463.14 911.72 496.89 892.99 559.95 882.4 592.23 865.53 647.17 802.71 775.76 761.69 827.74 l 811.45 815.91 b 819.46 814.43 826.61 816.41 811.95 839.56 800.37 849.91 786.57 852.37 769.58 853.36 l 749.87 855.82 b 735.95 867.52 732.26 873.68 717.84 873.58 719.75 864.81 724.93 863.82 710.45 866.66 669.33 879.25 583.17 897.04 528.58 901.38 l 493.56 266.68 676.15 19.92 722.82 11.89 b 782.31 72.28 879.98 188.22 918.82 247.32 921.64 230.66 921.9 196.63 924.36 181.4 925.13 173.12 928.62 177.69 930.99 179.79 942.85 191.39 946.88 195.95 947.64 207.55 l 943.88 289.74 b 949.03 301.16 957.9 317.9 954.63 329.5 950.06 331.56 946.48 331.02 941.38 326.27)"  # noqa
clipb = r"\iclip(m 776.85 12.37 b 814.9 48.64 885.77 124.93 918.57 167.94 917.91 162.79 916.23 152.48 915.95 147.32 l 916.7 72.72 b 921.48 53.7 935.16 66.63 939.94 68.6 954.84 80.88 967.4 106.56 967.69 117.71 974.91 145.73 978.09 205.9 974.06 240.29 981.84 255.1 995.15 277.59 1000.68 293.52 1001.99 304.49 1002.37 315.55 996.93 320.89 992.15 327.26 977.72 294.65 970.31 289.4 968.59 290.02 969.1 290.11 968.7 292.54 968.05 309.78 965.27 341.77 962.48 359.5 955.45 400.41 933.76 472.05 922.13 513.64 907 564.62 875.65 664.39 858.7 714.64 l 906.86 695.41 b 918.17 694.01 917.22 697.62 915.38 706.96 908.78 737.05 881.62 770.45 857.54 781.14 l 831.4 789.88 b 824.31 804.54 809.49 832.72 795.89 842.66 788.52 848.08 788.11 842.46 789.86 836.96 l 804.85 794.77 b 757.12 814.68 659.87 834.64 608.72 837.94 l 479.21 33.11)"  # noqa
clipc = r"\iclip(m 739.15 17.23 b 800.7 57.63 887.11 146.62 931.16 190.12 l 935.73 125.58 b 937.43 120.68 942.4 123.74 944.76 125.3 950.05 129.6 959.22 137.5 961.69 142.51 963.23 152.15 961.55 169.33 961.5 178.27 l 958.5 220.37 974 257.71 973.3 268.28 970.31 269.16 969.25 269.69 968.02 268.11 952.34 277.62 b 949.12 302.72 943.57 343.41 939.65 363.23 934.01 394.32 921.68 455.8 914.99 487.59 l 867.43 665.16 409.84 770.5 484.24 23.51)"  # noqa


def write_ass(filename: str, ass_data: AssFile):
    with open(filename, "w", encoding="utf-8") as fp:
        # BOM header, since some UTF fail
        fp.write("\ufeff")
        fp.write(ass_data.script_info.to_ass_string().rstrip() + "\n\n")
        fp.write(ass_data.styles.to_ass_string().rstrip() + "\n\n")
        fp.write(ass_data.events.to_ass_string().rstrip() + "\n")
        for section in ass_data.extra_sections:
            fp.write("\n")
            fp.write(section.to_ass_string().rstrip() + "\n")


def read_ass(filename: str) -> AssFile:
    ass_file = AssFile()
    with open(filename, "r", encoding="utf-8") as fp:
        ass_file.consume_ass_stream(fp)
    return ass_file


# pattern matching
# top = "m 19.006 50.91 l 109.136 34.53 102.136 0.56 9.276 15.92"
# first = ""
# second = ""
# third = ""
# fourth = "m 1.76 6.59 l 277.74 -39.1 284.33 -2.2 254.01 36.91 9.67 74.26 3.96 41.74"

in_ass = read_ass("bocchi02.ts.ass")
print("applying clip")
added = 0
for line in in_ass.events:
    if not line.is_comment:
        continue
    if "luine" not in line.actor:
        continue
    close_tag = line.text.find("}")
    before = line.text[:close_tag]
    after = line.text[close_tag:]
    match line.effect:
        case "a":
            clip = clipa
        case "b":
            clip = clipb
        case "c":
            clip = clipc
        case _:
            continue
    line.text = f"{before}{clip}{after}"
    line.is_comment = False
    added += 1

if added > 0:
    print("writing back!")
    write_ass("bocchi02.ts.ass", in_ass)
    print(f"updated {added} lines")
else:
    print("no match, ignoring")
