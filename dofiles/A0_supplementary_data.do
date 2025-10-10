/*------------------------------------------------------------------------------------------------------------

    Link parents and children by bith order

------------------------------------------------------------------------------------------------------------*/

use "/home2/rawdata3/AN_Lev_Barn.dta", clear

rename lopnr parent 
rename lopnr_barn child

** we keep adopted children now
drop if bioadop=="Adop"
drop bioadop


** Match gender, years of birth, and birth place of parents (second generation)
rename parent id_person
merge m:1 id_person using "${general_data}/clean_demografi.dta", keep(match master) keepusing(gender)
drop if mi(gender)
drop _merge
rename id_person parent 

** keep children with both parents identified in the data
gcollapse (nunique) n_p = parent, by(child) fast merge 
tab n_p
keep if n_p==2 //96.7 percent of children have both parents identified
drop n_p

**drop the same-gender parents
bysort child : gen homo=1 if (gender[_n+1] == gender[_n]) | (gender[_n-1] == gender[_n])
drop if homo==1
drop homo

save "${root_dir}/data/A0_1_clean_family.dta", replace



** indentifying each individuals' parents 
greshape wide parent, by(child) keys(gender) 

label variable parent1 "Father"
label variable parent2 "Mother"
save "${root_dir}/data/A0_1_clean_family_reshaped.dta", replace



/*------------------------------------------------------------------------------------------------------------

    clean wealth data

------------------------------------------------------------------------------------------------------------*/
use id_person year FNETTMV using "${general_data}/clean_wealth.dta", clear 
gcollapse (count) n=year, by(id_person year) fast merge
keep if n==1
drop n 
save "${root_dir}/data/A0_2_clean_wealth.dta", replace







// ren id_person1 father
// ren id_person2 mother


// ** include children's gender and years of birth 
// rename lopnr_barn id_person
// merge m:1 id_person using "${general_data}/clean_demografi.dta", keep (match master) keepusing (yob mob)
// drop _merge


// ** number of children
// bysort father mother: gen number_child=_N
// label variable number_child "Number of Children"
// sum number_child
// drop number_child

// ** years of birth
// hashsort father mother yob mob
// by father mother: gen order=_n

// drop yob mob
// rename id_person child
// reshape wide child, i(father mother) j(order)

// compress
// drop child7-child18
// save "/home/workgroups/crowdout/data/A1_4_clean_family.dta", replace