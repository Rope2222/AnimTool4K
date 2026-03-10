import os
import json

def load_meta_uuid_map(base_path, useFileName = False):
    """建立 meta sprite uuid 對照表：相對路徑 → uuid"""
    meta_map = {}

    for root, _, files in os.walk(base_path):
        for f in files:
            if f.endswith(".meta"):
                full = os.path.join(root, f)
                if(useFileName):
                    fileKey = os.path.splitext(f)[0]
                else:
                    fileKey = os.path.relpath(full, base_path)

                try:
                    with open(full, "r", encoding="utf-8") as fp:
                        data = json.load(fp)

                    # 尋找 subMetas 裡的 uuid
                    if "subMetas" in data:
                        for k, v in data["subMetas"].items():
                            if "uuid" in v:
                                meta_map[fileKey] = v["uuid"]
                except:
                    pass

    return meta_map


def find_anim_sprite_usage(anim_path):
    """回傳 anim 中使用到的所有 sprite uuid"""
    try:
        with open(anim_path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
    except:
        return []

    used = []

    def search(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "__uuid__":
                    used.append(v)
                search(v)
        elif isinstance(obj, list):
            for v in obj:
                search(v)

    search(data)
    return used


def replace_uuid_in_anim(anim_path, old_to_new):
    """將 anim 檔案裡的 uuid 依照 old_to_new 替換"""
    try:
        with open(anim_path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
    except:
        return

    def replace(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "__uuid__" and v in old_to_new:
                    obj[k] = old_to_new[v]
                else:
                    replace(v)
        elif isinstance(obj, list):
            for v in obj:
                replace(v)

    replace(data)

    with open(anim_path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)


def process(mode, path1, path2):
    print("\n掃描參考位置的 meta...")
    meta1 = load_meta_uuid_map(path1, mode == 'B')

    print("掃描修改位置的 meta...")
    meta2 = load_meta_uuid_map(path2, mode == 'B')

    print("\n開始掃描參考位置的 anim...\n")

    if(mode == 'A'):
        for root, _, files in os.walk(path1):
            for f in files:
                if f.endswith(".anim"):
                    anim_full1 = os.path.join(root, f)
                    anim_rel = os.path.relpath(anim_full1, path1)

                    used_uuids = find_anim_sprite_usage(anim_full1)
                    if not used_uuids:
                        continue

                    print("------------------------------------------------")
                    print(f"[動畫] {anim_rel}")

                    # 找 meta1（參考位置）
                    matched_meta1 = []
                    for rel, uuid in meta1.items():
                        if uuid in used_uuids:
                            matched_meta1.append((uuid, rel))
                            print(f"  - sprite uuid：{uuid}")
                            print(f"    參考位置 meta：{rel}")

                    # 修改位置的動畫位置
                    anim_full2 = os.path.join(path2, anim_rel)
                    if not os.path.exists(anim_full2):
                        print("  [警告] 修改位置 找不到對應的 anim")
                        continue

                    # 替換 uuid
                    uuid_replace_map = {}

                    for uuid, meta1_path in matched_meta1:
                        # 尋找修改位置 中 meta 的相對路徑
                        if meta1_path in meta2:
                            new_uuid = meta2[meta1_path]
                            uuid_replace_map[uuid] = new_uuid
                            print(f"    修改位置新 uuid：{new_uuid}")
                        else:
                            print("    [警告] 修改位置 找不到相對路徑的 meta")

                    if uuid_replace_map:
                        replace_uuid_in_anim(anim_full2, uuid_replace_map)
                        print("  → 已更新修改位置的 anim UUID")
    else: # mode B
        for root, _, files in os.walk(path1):
            for f in files:
                if f.endswith(".anim"):                
                    anim_full1 = os.path.join(root, f)
                    anim_rel = os.path.relpath(anim_full1, path1)
                    anim_file_name1 = os.path.splitext(f)[0]

                    used_uuids = find_anim_sprite_usage(anim_full1)
                    if not used_uuids:
                        continue

                    print("------------------------------------------------")
                    print(f"[動畫] {anim_rel}")

                    # 找 meta1（參考位置）
                    matched_meta1 = []
                    for rel, uuid in meta1.items():
                        if uuid in used_uuids:
                            matched_meta1.append((uuid, rel))
                            print(f"  - sprite uuid：{uuid}")
                            print(f"    參考位置 meta：{rel}")

                    # 修改位置的動畫位置
                    for root2, _2, files2 in os.walk(path2):
                        for f in files2:
                            if f.endswith(".anim"):
                                anim_file_name2 = os.path.splitext(f)[0]
                                if(anim_file_name2 == anim_file_name1):
                                    anim_full2 =  os.path.join(root2, f)
                                    # 替換 uuid
                                    uuid_replace_map = {}

                                    for uuid, meta1_path in matched_meta1:
                                        # 尋找修改位置 中 meta 的檔名
                                        if meta1_path in meta2:
                                            new_uuid = meta2[meta1_path]
                                            uuid_replace_map[uuid] = new_uuid
                                            print(f"    修改位置新 uuid：{new_uuid}")
                                        else:
                                            print("    [警告] 修改位置 找不到對應檔名的 meta")

                                    if uuid_replace_map:
                                        replace_uuid_in_anim(anim_full2, uuid_replace_map)
                                        print("  → 已更新修改位置的 anim UUID")





if __name__ == '__main__':
    print('選擇模式:')
    print('A = 路徑比對')
    print('B = 檔名比對')
    mode = input('輸入 A 或 B: ').strip().upper()
    if mode not in ['A','B']:
        print('模式錯誤')
        exit()

    p1 = input('來源路徑 Path1: ').strip()
    p2 = input('修改路徑 Path2: ').strip()

    process(mode, p1, p2)
    input('\n完成! 按 Enter 離開...')