



use "${root_dir}/data/A0_1_clean_family_reshaped.dta", clear

** children year of birht to find the first child of each couple 
rename child id_person
merge m:1 id_person using "${general_data}/clean_demografi.dta", keep(match master) keepusing(yob country_of_birth_iso)
rename id_person child
drop _merge

** keep the first child of each couple 
hashsort parent1 parent2 yob 
by parent1 parent2: keep if _n==1

keep if country_of_birth_iso==187
drop country_of_birth_iso

* the child id can work as spouse id now.
rename child id_spouse 

* the yob of the child works as the matching year of the couple
rename yob t_match 
keep if inrange(t_match, 1970, 2019)


** merge with parent-child data to find the spouse's parents (i.e., the other set of grandparents) 
// greshape long parent, by(id_spouse) keys(g_parent) 

rename parent1 child 
rename parent2 mother 
merge m:1 child using "${root_dir}/data/A0_1_clean_family_reshaped.dta", keep(match master) keepusing(parent1 parent2)
rename parent1 parent11 
rename parent2 parent12 

rename child father 
rename mother child 
capture drop _merge
merge m:1 child using "${root_dir}/data/A0_1_clean_family_reshaped.dta", keep(match master) keepusing(parent1 parent2)
rename parent1 parent21
rename parent2 parent22 
rename child parent2 
rename father parent1

* check missing grandparents 
gen notmissing = 0 if mi(parent11) | mi(parent12) | mi(parent21) | mi(parent22) 
replace notmissing = 1 if notmissing==.
tab notmissing

preserve 
gcollapse (mean) notmissing , by(t_match) fast 
replace notmissing = notmissing*100

graph twoway (line notmissing t_match, lcolor(navy) lwidth(thick) lpattern(solid)), ///
    title("share of each birth cohort with identified grandparents") ///
    xtitle("Matching year (year of first child's birth)") ///
    ytitle("Share of children with identified grandparents") ///
    ylabel(0(10)100, format(%9.0f)) ///
    legend(off) graphregion(color(white)) 

restore 

drop notmissing _merge 

** add parents information step-by-step 
greshape long parent, by(id_spouse) keys(g_parent)
drop if mi(parent) 
rename parent id_person

** demographic information of parents
merge m:1 id_person using "${general_data}/clean_demografi.dta", keep(match master) keepusing(yob lan_of_birth country_of_birth_iso) nogenerate 
rename lan_of_birth lob 
rename country_of_birth_iso cob 
gen swede = 1 if cob==187 

** income information 
gen year = t_match - 5
merge m:1 id_person year using "${general_data}/iot_income.dta", keep(match master) keepusing(earnings_work5) nogenerate
rename earnings_work5 income

** registered lcoation at time of matching 
replace year = t_match 
merge m:1 id_person year using "${general_data}/clean_boende.dta", keep(match master) keepusing(lan kommun) nogenerate

** wealth information  
replace year = t_match - 5 
merge m:1 id_person year using "${root_dir}/data/A0_2_clean_wealth.dta", keep(match master) keepusing(FNETTMV) nogenerate
rename FNETTMV wealth 

** education information 
merge m:1 id_person using "${general_data}/education_max.dta", keep(master matched) keepusing(SUN2000Niva_old_max) nogenerate
rename SUN2000Niva_old_max educ 

** reshape data to wide format 
drop year 
rename id_person parent

** drop if location for either spouse is missing
capture drop miss_lan
gen miss_lan = 1 if mi(lan) & (g_parent==1 | g_parent==2)
replace miss_lan = 0 if miss_lan==.
gcollapse (max) miss_lan , by(id_spouse) fast merge replace
drop if miss_lan==1
drop miss_lan

preserve 
    keep if inlist(g_parent,1,11,12)
    greshape wide parent lob-educ, by(id_spouse) keys(g_parent)
    save "${root_dir}/data/A1_1_couples_info_man.dta", replace
restore 
preserve 
    keep if inlist(g_parent,2,21,22)
    greshape wide parent lob-educ, by(id_spouse) keys(g_parent)
    save "${root_dir}/data/A1_1_couples_info_woman.dta", replace
restore 

greshape wide parent lob-educ, by(id_spouse) keys(g_parent)
save "${root_dir}/data/A1_1_couples_info.dta", replace

// ** save data for men and women separately 
// greshape long parent, by(id_spouse) keys(g_parent)

** document missing infromation on location


preserve 
gen miss_lan = 1 if mi(lan1) | mi(lan2)
replace miss_lan = 0 if miss_lan==.
keep if t_match>=1990
gcollapse (mean) miss_lan , by(t_match) fast 
replace miss_lan = miss_lan*100

graph twoway (line miss_lan t_match, lcolor(navy) lwidth(thick) lpattern(solid)), ///
    title("share with missing location information") ///
    xtitle("Matching year (year of first child's birth)") ///
    ytitle("Share with missing location information") ///
    ylabel(0(10)100, format(%9.0f)) ///
    legend(off) graphregion(color(white)) 

restore 

** different lan codes for matched couples
preserve
drop if mi(lan1) | mi(lan2)
gen diff_lan = (lan1!=lan2)
gcollapse (mean) diff_lan , by(t_match) fast
replace diff_lan = diff_lan*100

graph twoway (line diff_lan t_match, lcolor(navy) lwidth(thick) lpattern(solid)), ///
    title("share of couples with different registered lan") ///
    xtitle("Matching year (year of first child's birth)") ///
    ytitle("Share of couples with different registered lan") ///
    ylabel(0(10)40, format(%9.0f)) ///
    legend(off) graphregion(color(white))

restore