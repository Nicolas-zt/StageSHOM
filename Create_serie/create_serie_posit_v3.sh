#!/bin/bash

print_usage(){ echo "$(basename $0) creates position time series in SPOTGINS format.

	OPTIONS : 
		-ac    ^= Analysis Center (3-4 characters)
		-name  ^= Station name (9 characters)
		-help   = print this.


	OUTPUT : Spotgins position time series (in ${series_dir}/ folder).

	USAGE : bash $(basename $0) -ac EOST -name BRST00FRA

	WARNING : the GINS solutions must contain at least GPS data, and possibly GALILEO data as well.
" 1>&2; exit 1; }

#########################
# DEFINITION OF VARIABLES
#########################
SPOTGINS_DIR=.
if [[ -z $SPOTGINS_DIR ]]; then
	echo "$(basename $0) FATAL ::: \$SPOTGINS_DIR is not defined"
	echo This environment variable contains the path to the spotgins root folder
	exit 1
fi
version="v3"
rand=$(echo $RANDOM)


#######
# INPUT
#######
if [[ ! $1 ]]; then
	print_usage
fi

ac=""
name=""

while (($# > 0)) # $# = nbre d'arguments restants. il diminue de 1 à chaque fois qu'on shift
do
	option=$1
	param=${option#*=}
	if [ "${param}" = "${option}" ]; then param= ; fi
	if [ -n "${param}" ]; then option=${option%=*} ; fi

	case ${option} in
	-ac*)
		if [ -n "${param}" ]; then
			ac=${param^^}
		elif [ ${#option} -gt 3 ]; then
			ac=$(echo ${option#"-ac"} | tr [[:lower:]] [[:upper:]])
		else
			shift
			ac=${1^^}
		fi
		;;

	-name*)
		if [ -n "${param}" ]; then
			name=${param^^}
		elif [ ${#option} -gt 5 ]; then
			name=$(echo ${option#"-name"} | tr [[:lower:]] [[:upper:]])
		else
			shift
			name=${1^^}
		fi
		;;

	-help*)
		echo ""
		print_usage
		;;

	*)
		echo "$(basename $0) FATAL ::: BAD OPTION"
		echo ""
		print_usage
		;;

	esac
	shift
done


##############
# VERIFICATION
##############
if [[ ! ${ac} =~ ^[A-Z,0-9]{3,4}$ ]]; then
	echo "$(basename $0) FATAL ::: BAD INPUT AC"
	echo ""
	print_usage
fi

if [[ ! ${name} =~ ^[A-Z,0-9]{4}[0-9]{2}[A-Z]{3}$ ]]; then
	echo "$(basename $0) FATAL ::: BAD INPUT NAME"
	echo ""
	print_usage
fi
stations_dir="${SPOTGINS_DIR}/station"
scripts_dir="${POSPRECIS_PATH}/SCRIPTS_SPOTGINS/COMMUN/python"
series_dir="${SPOTGINS_DIR}/series"
listing_dir="${SPOTGINS_DIR}/listing/${name:0:4}"
stats_dir="${SPOTGINS_DIR}/statistiques/${name:0:4}"
solution_dir="${SPOTGINS_DIR}/result/TORK_test/Corrected"
log_file="${SPOTGINS_DIR}/series/serie.log"
file_sol="${series_dir}/${name}.enu"
mkdir -p ${series_dir}
rm $log_file

if [[ ! -d "${listing_dir}" ]] || [[ ! -d "${stats_dir}" ]] || [[ ! -d "${solution_dir}" ]]; then
	echo "$(basename $0) FATAL ::: The listing, statistics or solution directories are not found"
        exit 1
fi

if [[ -f ${file_sol} ]]; then
	# A series file for this station already exists, checking its version
	ver=$(grep "# SPOTGINS SOLUTION \[POSITION\] " ${file_sol} | awk '{ print $5 }')
	if [[ -z "$ver" ]] || [[ $ver != $version ]]; then
		echo "$(basename $0) FATAL ::: ${file_sol} already exists with a different file version"
		exit 1
	fi
fi

###############################
# SEARCH STATION IN MASTER FILE
###############################
masterInfo=$(grep " ${name} " ${stations_dir}/station_master_file.dat)
if [[ ${masterInfo} == "" ]]; then
	echo "$(basename $0) FATAL ::: Station ${name} is not in the master file"
	exit 1
fi
acmaster=$(echo ${masterInfo} | awk '{ print $1 }')
if [[ ${#acmaster} -eq 0 ]] || ([[ ${acmaster} != ${ac} ]] && [[ ${acmaster} != "ALL" ]]); then
	echo "$(basename $0) FATAL ::: Station ${name} is not attributed to ${ac}"
	exit 1
fi
domes=$(echo ${masterInfo} | awk '{print $3}')
Xref=$(echo ${masterInfo} | awk '{printf "%15.6f", $7}')
Yref=$(echo ${masterInfo} | awk '{printf "%15.6f", $8}')
Zref=$(echo ${masterInfo} | awk '{printf "%15.6f", $9}')
lon=$(echo ${masterInfo} | awk '{printf "%11.6f", $5}')
lat=$(echo ${masterInfo} | awk '{printf "%11.6f", $4}')
hei=$(echo ${masterInfo} | awk '{printf "%11.6f", $6}')
data_src=$(echo ${masterInfo} | awk '{print $11}')


############################################
# EXTRACTION OF DATA FROM THE SOLUTION FILES
############################################
# look for solution files and for each day take only the last that was computed
ls ${solution_dir} | grep -v ".*txt" | grep "${name}.*IPPP" | sed "s/${name}_\([0-9]\{4\}_[0-9]\{3\}\).*\([0-9]\{6\}_[0-9]\{6\}\).gins.IPPP/\1 \2/" | sort -k1,1 -k2,2r | awk '!seen[$1]++' > ${file_sol}.files.$rand
#we must divide the search per year if we dont want to have a too long argument list due to limitations with the python script
for year in $(seq 2000 $(date "+%Y")); do
	XYZ=$(while read epoch1 epoch2; do grep -hE "^XYZ_SOL" ${solution_dir}/*${name}_${epoch1}*${epoch2}.gins.IPPP 2> /dev/null | sort -k3,3n; done < <(grep "^${year}_" ${file_sol}.files.$rand))
	if [[ ! -z "${XYZ}" ]]; then
		jjul0=$(jjul 01 01 $year | grep "JUL50" | awk '{ print $3 }')
		days_in_year=$(date -d "$year-12-31" +%j)
		XYZ_coord=$(echo "${XYZ}" | awk '{printf "%.15e %.15e %.15e\n", $5, $7, $9}')
		coord_enu=$(python ${scripts_dir}/xyz2enu_coord.py ${Xref} ${Yref} ${Zref} "${XYZ_coord}" | sed '1d')
		XYZ_covar=$(echo "${XYZ}" | awk '{printf "%.15e %.15e %.15e %.15e %.15e %.15e %.15e %.15e %.15e\n", $5, $7, $9, $10, $11, $12, $13, $14, $15}')
		covar_enu=$(python ${scripts_dir}/xyz2enu_covar.py "${XYZ_covar}" | sed '1d')
		if [[ $? -ne 0 ]]; then
			echo "Problem transforming XYZ coordinates to ENU coordinates for site ${name} and year ${year}" >&2
		fi
		dates=$(echo "${XYZ}" | awk '{print $2, $3}')
		echo "${dates}"
		paste <(echo "${dates}") <(echo "${coord_enu}") <(echo "${covar_enu}") |
		awk -v jjul0="$jjul0" -v year="$year" -v diy="$days_in_year" '
		{
			x=$3; y=$4; z=$5;
			
			gsub(/[(),]/,"",x);
			gsub(/[(),]/,"",y);
			gsub(/[(),]/,"",z);
			
			cxx=$6; cyy=$7; czz=$8;
			cxy=$9; cxz=$10; cyz=$11;

			gsub(/[(),]/,"",cxx);
			gsub(/[(),]/,"",cyy);
			gsub(/[(),]/,"",czz);
			gsub(/[(),]/,"",cxy);
			gsub(/[(),]/,"",cxz);
			gsub(/[(),]/,"",cyz);

			printf " %6.1f %14.6f %14.6f %14.6f %14.6f %14.6f %14.6f %10.6f %10.6f %10.6f  %4s-%2s-%2sT12:00:00  %11.6f\n",
				   int($2)+33282.5,
				   x, y, z,
				   sqrt(cxx), sqrt(cyy), sqrt(czz),
				   cxy/sqrt(cxx*cyy),
				   cxz/sqrt(cxx*czz),
				   cyz/sqrt(cyy*czz),
				   substr($1,1,4), substr($1,6,2), substr($1,9,2),
				   year+(int($2)+0.5-jjul0)/diy
		}' |
		sort -u -k1,1 |
		awk '!a[$1]++' >> "${file_sol}.new.$rand"	
		cat "${file_sol}.new.$rand"
		fi
done
if [ ! -f ${file_sol}.new.$rand ]; then
	echo "No solutions found for station ${name} in ${solution_dir}. The SPOTGINS series was not created."
	exit
fi
########################################################
# EXTRACTION OF DATA FROM THE LISTING & STATISTICS FILES
########################################################
Qflag=()
date_of_exe=()
version_gins=()
version_prairie=()
constel=()
while read epoch1 epoch2; do
	echo "${epoch1} ${epoch2}"
	year=$(echo $epoch1 | awk -F_ '{ print $1 }')
	doy=$(echo $epoch1 | awk -F_ '{ print $2 }')
	file_listing=$(find ${listing_dir} \( -name "*${name}_${epoch1}*${epoch2}*.gins" \))
	file_stat=$(find ${stats_dir} \( -name "*${name}_${epoch1}*${epoch2}.gins.0" \))
	#file_prairie=$(find ${listing_dir} \( -name "*${name}_${epoch1}*.prairie" \)) 
	if [ ! -z ${file_listing} ] && [ ! -z ${file_stat} ]; then
	#if [ ! -z ${file_stat} ] ; then
		range=$(awk '{ print $2 }' ${file_stat} | sed -n '1p;$p' | paste -sd ' ' | awk '{ print $2-$1 }')
		epochs=$(awk '{ print $2 }' ${file_stat} | sort -n | uniq | wc -l)
		# check for duration of tracking
		flag_duration=$(echo $range $epochs | awk '{ if ( ($1 > 0.5) && ($2 > 144) ) print 0; else print 2 }')
		if [[ $flag_duration -ne 0 ]]; then
			echo -e "Flag durée de mesure : ${flag_duration} ${file_stat}\n" >> $log_file
		fi
		# check for calibrated antenna (only for 25_1 and earlier)
		flag_antex1=$(grep "(G-lec_affecte_antex14" ${file_listing} | grep station | wc -l | awk '{ if ($1 > 0) print 1; else print 0 }')
		if [[ $flag_antex1 -ne 0 ]]; then
			echo -e "Flag 1 calibration antenne : ${flag_antex1} ${file_listing}\n" >> $log_file 
		fi
		# check for calibrated frequency (only for 25_1 and earlier)
		flag_antex2=$(grep "(G-antex_orig_mod) " ${file_listing} | grep GPS12 | wc -l | awk '{ if ($1 > 1) print 1; else print 0 }')
		if [[ $flag_antex2 -ne 0 ]]; then
			echo -e "Flag 2 calibration antenne : ${flag_antex2} ${file_listing}\n" >> $log_file 
		fi
		# check for calibrated radome
		flag_antex3_v25_1=$(grep "(G-lec_affecte_antex) :" ${file_listing} | grep radome | wc -l | awk '{ if ($1 > 0) print 1; else print 0 }')
		flag_antex3_v25_2=$(grep "(G-gestion_antex_mod) : remplacement du type de radome par NONE pour antenne" ${file_listing} | wc -l | awk '{ if ($1 > 0) print 1; else print 0 }')
		flag_antex3=$(echo $flag_antex3_v25_1 $flag_antex3_v25_2 | awk '{ if ($1+$2 > 0) print 1; else print 0 }')
		if [[ $flag_antex3 -ne 0 ]]; then
			echo -e "Flag 3 calibration antenne : ${flag_antex3} ${file_listing}\n" >> $log_file 
		fi
		# summary of antex flag
		flag_antex=$(echo $flag_antex1 $flag_antex2 $flag_antex3 | awk '{ if ($1+$2+$3 > 0) print 1; else print 0 }')
		if [[ $flag_antex -ne $flag_antex3 ]]; then
			echo -e "Flag antex 25_1 non nul : ${flag_antex} ${flag_antex3} ${file_listing}\n" >> $log_file
		fi 
		if [[ $flag_antex -ne 0 ]]; then
			echo -e "Flag antex total : ${flag_antex} ${file_listing}\n" >> $log_file
		fi 
		# check for fixed ambiguities
		flag_fixAmbis=$(grep -A10 " GPh      GRa     GBlo " ${file_listing} | grep " 5: " | awk '{ if ( (($6 > 0) && ($6 < 80)) || (($18 > 0) && ($18 < 80)) ) print 4; else print 0 }')
		if [[ $flag_fixAmbis -ne 0 ]]; then
			echo -e "Flag 4 fixation ambiguïtés : ${flag_fixAmbis} ${file_listing}\n" >> $log_file 
		fi
		Qflag+=$(echo $flag_antex $flag_duration $flag_fixAmbis | awk '{ printf "\n%d\n", $1 + $2 + $3 }')
		#echo -e "FLAG TOTAL : ${epoch1} ${Qflag} ${flax_antex}" >> $log_file
		# Constellation
        pres_gps=$(grep -m 1 "RAPH_GPS:CC" ${file_listing} | wc -l)
        pres_gal=$(grep -m 1 "RAPH_GAL:CC" ${file_listing} | wc -l)
        const=""
        if [[ "$pres_gps" -eq 1 ]]; then
            const="G"
            if [[ ! $const_head == "G"* ]]; then
                const_head="G${const_head}"
            fi
        fi
        if [[ "$pres_gal" -eq 1 ]]; then
            const="${const}E"

           if [[ ! $const_head == *"E" ]]; then
               const_head="${const_head}E"
           fi
        fi
        constel+=$(printf "\n${const}\n")

		version_gins+=$(out=$(grep -m 1 "#GINS_VERSION" ${solution_dir}/*${name}_${epoch1}*${epoch2}.gins.IPPP 2> /dev/null); echo $out | awk '{print ($0 ? $2 : "Unknown")}' | xargs printf "\n%s\n")
		#version_prairie+=$(out=$(grep -m 1 "Prog is prairie" ${file_listing} 2> /dev/null); echo $out | awk '{print ($5 ? $5 : "Unknown")}' | xargs printf "\n%s\n")
		#version_prairie+=$(out=$(grep -m 1 'PRAIRIE\.v' "${file_prairie}" 2> /dev/null | sed -E 's/.*PRAIRIE\.(v[0-9]{2}).*/\1/'); echo $out | awk '{print ($1 ? $1 : "Unknown")}' | xargs printf "\n%s\n")
		date_of_exe+=$(echo "${file_listing}" | awk 'NR==1 {print $NF}' | rev | cut -c6-18 | rev | xargs printf "\n%s\n")
	else
		echo Missing listing and/or statistics file for ${name}_${year}_${doy}
		Qflag+=$(echo NA | xargs printf "\n%s\n")
		constel+=$(echo NA | xargs printf "\n%s\n")
		version_gins+=$(echo NA | xargs printf "\n%s\n")
		version_prairie+=$(echo NA | xargs printf "\n%s\n")
		date_of_exe+=$(echo NA | xargs printf "\n%s\n")
	fi
done < ${file_sol}.files.$rand
echo "Fin traitement listings"

###################################################
# MERGING ALL THE DATA COLUMNS INTO THE SERIES FILE
###################################################
man_plz=$(paste -d ' ' ${file_sol}.new.$rand <(printf " %-5s\n" $constel))
echo "$man_plz" > ${file_sol}.new.$rand
man_plz=$(paste -d ' ' ${file_sol}.new.$rand <(printf " %4s\n" $Qflag))
echo "$man_plz" > ${file_sol}.new.$rand
man_plz=$(paste -d ' ' ${file_sol}.new.$rand <(printf " %-13s\n" $date_of_exe))
echo "$man_plz" > ${file_sol}.new.$rand
man_plz=$(paste -d ' ' ${file_sol}.new.$rand <(printf " %-11s\n" $version_gins))
echo "$man_plz" > ${file_sol}.new.$rand
man_plz=$(paste -d ' ' ${file_sol}.new.$rand <(printf " %3s\n" $version_prairie))
echo "$man_plz" > ${file_sol}.new.$rand
now_date=$(date -u "+DATE             : %Y-%m-%d at %H:%M:%S (UTC)")

# removing invalid points
sed -i '/ NA /d' ${file_sol}.new.$rand


############################
# MERGING NEW AND OLD SERIES
############################
if [[ -f ${file_sol} ]]; then
	# merge old and new series keeping new values over old ones
	echo File ${file_sol} already exists and will be updated.
	# extract old values
	grep -v "^#" ${file_sol} > ${file_sol}.old.$rand
	# extract old and new epochs using first column (julidan days)
	awk '{ print $1 }' ${file_sol}.old.$rand | sort | uniq > ${file_sol}.old.epochs.$rand
	awk '{ print $1 }' ${file_sol}.new.$rand | sort | uniq > ${file_sol}.new.epochs.$rand
	# extract old values that were not updated
	comm -23 ${file_sol}.old.epochs.$rand ${file_sol}.new.epochs.$rand | awk '{ print $1 }' | sed 's/^/\^ /' | sed 's/$/ /' > ${file_sol}.keep.epochs.$rand
	grep -f ${file_sol}.keep.epochs.$rand ${file_sol}.old.$rand > ${file_sol}.old.keep.$rand
	if [ -f ${file_sol}.old.keep.$rand ];then
		mv ${file_sol}.old.keep.$rand ${file_sol}.old.$rand # old file is shortened to the non-updated values only
	else
		> ${file_sol}.old.$rand # empty file, all the old points were updated
	fi
	# join the new and the old (not updated) values
	cat ${file_sol}.old.$rand ${file_sol}.new.$rand > ${file_sol}.temp.$rand
	mv ${file_sol}.temp.$rand ${file_sol}.new.$rand
	# checking and cleaning
	rm -f ${file_sol}.new.epochs.$rand ${file_sol}.keep.epochs.$rand ${file_sol}.old* ${file_sol}.temp.$rand
fi


########################
# CREATION OF THE HEADER
########################
now_date=$(date -u "+Creation %Y-%m-%d at %H:%M:%S (UTC)")
# extract the constellation value for the series header
ge=$(awk '{ if($13=="GE") print $13 }' ${file_sol}.new.$rand | wc -l)
if [[ $ge -gt 0 ]]; then
	const="GE"
else
	const="G"
fi

echo "# SPOTGINS SOLUTION [POSITION] ${version}
# ${now_date}
#----------------------------------------------------------
# STATION          : ${name}
# ANALYSIS_CENTRE  : ${ac}
# STRATEGY_SUMMARY : https://www.poleterresolide.fr/geodesy-plotter/#/solution/SPOTGINS
# REF_FRAME        : IGS20
# PRODUCTS         : G20/GRG
# CONSTELLATION    : ${const_head}
# UNITS            : meters
# ELLIPSOID        : GRS80
# DATA_SOURCE      : ${data_src}
# FLAG             : 0 = Full quality
# FLAG             : 1 = Antenna/radome not calibrated
# FLAG             : 2 = Less than 12 h of observations
# FLAG             : 4 = Less than 80% of fixed ambiguities
# ACKNOWLEDGMENTS  :
#----------------------------------------------------------
# X_pos            : ${Xref}
# Y_pos            : ${Yref}
# Z_pos            : ${Zref}
# Longitude        : ${lon}
# Latitude         : ${lat}
# Height           : ${hei}
#----------------------------------------------------------
#MJD           DispEast      DispNorth         DispUp      SigmaEast     SigmaNorth        SigmaUp     CorrEN     CorrEU     CorrNU  yyyy-mm-ddTHH:MM:SS  DecimalYear  Const  Flag  DateOfExe      GinsVersion  PrairieVersion" > ${file_sol}.head.$rand


###########################
# MERGING HEADER AND SERIES
###########################
cat ${file_sol}.new.$rand | sort -u -k1,1n > ${file_sol}.temp.$rand
cat ${file_sol}.head.$rand ${file_sol}.temp.$rand > ${file_sol}
rm -f ${file_sol}.new.$rand ${file_sol}.head.$rand ${file_sol}.temp.$rand ${file_sol}.files.$rand
echo ${file_sol}
