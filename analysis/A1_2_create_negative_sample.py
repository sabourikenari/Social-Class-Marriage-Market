
true_pairs = pd.read_stata("./data/A1_1_couples_info.dta")
men_df = pd.read_stata("./data/A1_1_couples_info_man.dta")
women_df = pd.read_stata("./data/A1_1_couples_info_woman.dta")

true_pairs = true_pairs[true_pairs['t_match'] == 2007]
men_df = men_df[men_df['t_match'] == 2007]
women_df = women_df[women_df['t_match'] == 2007]




# PARAMETERS
K = 100
rng = np.random.default_rng(42)

# --- Step 1. Clean duplicates and merge to create positive pairs ---
men_df_clean = men_df.drop(columns=['t_match'], errors='ignore')
women_df_clean = women_df.drop(columns=['t_match'], errors='ignore')

# Build fully-featured positive pairs with consistent suffixes
men_sfx = men_df_clean.add_suffix('_m').rename(columns={'id_spouse_m': 'id_spouse'})
women_sfx = women_df_clean.add_suffix('_w').rename(columns={'id_spouse_w': 'id_spouse'})
true_pairs_full = (
    true_pairs[['id_spouse']]
    .merge(men_sfx, on='id_spouse', how='left')
    .merge(women_sfx, on='id_spouse', how='left')
)
true_pairs_full['match'] = 1

# --- Step 2. Add partner province columns to men_df and women_df ---
# (so each man knows his wife's province and vice versa)
men_with_spouseprov = men_df.merge(
    true_pairs[['id_spouse', 'lan2']], on='id_spouse', how='left'
).rename(columns={'lan2': 'spouse_province'})

women_with_spouseprov = women_df.merge(
    true_pairs[['id_spouse', 'lan1']], on='id_spouse', how='left'
).rename(columns={'lan1': 'spouse_province'})

# --- Step 3. Efficient vectorized sampling with suffixes ---
def sample_negatives(
    df_source,
    df_target,
    province_col,
    target_province_col,
    K,
    source_suffix,
    target_suffix,
):
    """Sample K random opposite-sex individuals from same province and suffix columns.
    Returns a dataframe with columns suffixed as *_m for source side and *_w for target side (or vice versa),
    plus a 'match' column set to 0.
    """
    samples = []
    for prov, group_source in df_source.groupby(province_col):
        pool = df_target[df_target[target_province_col] == prov]
        if pool.empty or len(group_source) == 0:
            continue
        # Sample target side with replacement to match K per source row
        idx = rng.choice(pool.index, size=K * len(group_source), replace=True)
        sampled = pool.loc[idx].reset_index(drop=True)
        # Repeat source rows K times without index issues
        repeated = pd.concat([group_source] * K, ignore_index=True)
        # Apply suffixes to avoid duplicate column names
        repeated = repeated.add_suffix(source_suffix)
        sampled = sampled.add_suffix(target_suffix)
        # Combine sides column-wise
        pairs = pd.concat([repeated, sampled], axis=1)
        pairs['match'] = 0
        samples.append(pairs)
    return pd.concat(samples, ignore_index=True) if samples else pd.DataFrame()

# --- Step 4. Generate negatives ---
# men-based negatives: women from same province as man's actual wife
neg_from_men = sample_negatives(
    df_source=men_with_spouseprov,
    df_target=women_df,
    province_col='spouse_province',
    target_province_col='lan2',
    K=K,
    source_suffix='_m',
    target_suffix='_w',
)

# women-based negatives: men from same province as woman's actual husband
neg_from_women = sample_negatives(
    df_source=women_with_spouseprov,
    df_target=men_df,
    province_col='spouse_province',
    target_province_col='lan1',
    K=K,
    source_suffix='_w',
    target_suffix='_m',
)

# --- Step 5. Combine all ---
all_pairs = pd.concat([true_pairs_full, neg_from_men, neg_from_women], ignore_index=True)

print("Final data shape:", all_pairs.shape)
print(all_pairs['match'].value_counts())

# Optional: save
# all_pairs.to_parquet("marriage_pairs_for_xgb.parquet")



print("Men with missing spouse_province:", men_with_spouseprov['spouse_province'].isna().sum())
print("Women with missing spouse_province:", women_with_spouseprov['spouse_province'].isna().sum())

# check how many provinces skipped due to no opposite-sex pool
missing_provinces = set(men_with_spouseprov['spouse_province']) - set(women_df['lan2'])
print("Provinces with men but no women:", missing_provinces)

