import json
import re

def extract_numbers(text):
    # Find all sequences of digits, optionally with a decimal point
    nums = re.findall(r'\d+(?:\.\d+)?|\d+(?:,\d+)?', text)
    # Convert to float for comparison, replacing comma with dot
    res = []
    for n in nums:
        try:
            res.append(float(n.replace(',', '.')))
        except:
            pass
    return set(res)

def align():
    # 1. Load Markdown problems
    with open('problems/VNSchoolMathProblems2026/exam_problems.md', 'r', encoding='utf-8') as f:
         text = f.read()
    vn_problems = [p.strip() for p in re.findall(r"^\+ (.*?)$", text, re.MULTILINE)]
    
    # 2. Load JSON problems
    with open('problems/VNSchoolMathProblems.json', 'r', encoding='utf-8') as f:
        en_problems = json.load(f)
        
    n = len(vn_problems)
    m = len(en_problems)
    print(f"VN problems: {n}, EN problems: {m}")
    
    vn_nums = [extract_numbers(p) for p in vn_problems]
    en_nums = [extract_numbers(p['text']) for p in en_problems]
    
    # DP alignment
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            # score is the number of matching numbers
            match_score = len(vn_nums[i-1].intersection(en_nums[j-1]))
            # small penalty for matching to favor skipping when match_score is 0,
            # but wait, since EN problems MUST be a subsequence of VN problems,
            # we just need to find the monotonically increasing mapping j -> i(j)
            
    # Actually, a simpler DP for subsequence alignment:
    # dp[i][j] = max score of aligning first i VN and first j EN
    dp = [[-1000000] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = 0
        
    choice = [[0] * (m + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            # Option 1: skip this VN problem (it wasn't generated)
            skip_score = dp[i-1][j]
            
            # Option 2: match this VN problem with EN problem j
            match_score = len(vn_nums[i-1].intersection(en_nums[j-1]))
            # Jaccard similarity to be more robust
            union_len = len(vn_nums[i-1].union(en_nums[j-1]))
            if union_len == 0:
                score = 0
            else:
                score = match_score / union_len
            
            align_score = dp[i-1][j-1] + score + 0.1 # 0.1 bonus for aligning
            
            if align_score > skip_score:
                dp[i][j] = align_score
                choice[i][j] = 1
            else:
                dp[i][j] = skip_score
                choice[i][j] = 0
                
    # Backtrack
    i, j = n, m
    matched_vn_indices = []
    while i > 0 and j > 0:
        if choice[i][j] == 1:
            matched_vn_indices.append(i - 1)
            i -= 1
            j -= 1
        else:
            i -= 1
            
    matched_vn_indices.reverse()
    
    print(f"Matched {len(matched_vn_indices)} problems.")
    
    missing_indices = set(range(n)) - set(matched_vn_indices)
    missing_problems = [vn_problems[i] for i in sorted(list(missing_indices))]
    
    print(f"Missing {len(missing_problems)} problems:")
    
    with open('problems/missing_problems_temp.md', 'w', encoding='utf-8') as f:
        for p in missing_problems:
            f.write(f"+ {p}\n")
            print("-", p[:80], "...")

if __name__ == '__main__':
    align()
