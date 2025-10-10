



use "${root_dir}/data/A0_1_clean_family_reshaped.dta", clear

** children year of birht to find the first child of each couple 
rename child id_person
merge m:1 id_person using "${general_data}/clean_demografi.dta", keep(match master) keepusing(yob)
rename id_person child
drop _merge

** keep the first child of each couple 
hashsort parent1 parent2 yob 
by parent1 parent2: keep if _n==1

* the child id can work as spouse id now.
rename child id_spouse 

* the yob of the child works as the matching year of the couple
rename yob t_match 

