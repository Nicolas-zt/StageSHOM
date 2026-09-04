#!/bin/bash

print_usage(){ echo "$(basename $0) creates/updates the series of tropospheric products in SPOTGINS format from all the 'listing' files available for the station.

	OPTIONS : 
		-name  = Station name (9 characters)
		-help  = print this.


	OUTPUT : Spotgins tropo time series (in ${SPOTGINS_DIR}/../run/series folder).

	USAGE : bash $(basename $0) -name BRST00FRA

" 1>&2; exit 1; }

#TROTOT: délai tropo total (sec + humide)
#TRODRY: délai tropo sec ou hydrostatique (pression atm, valeur a priori)
#TROWET: délai tropo humide (vapeur d'eau, valeur estimée)
#STDWET: erreur du délai tropo
#TGNTOT/TGETOT: gradient tropo nord/est
#STDTGN/STDTGE : erreur gradient tropo nord/est

# INPUT
name=""

while (($# > 0)) # $# = nbre d'arguments restants. il diminue de 1 à chaque fois qu'on shift
do
	option=$1
	param=${option#*=}
	if [ "${param}" = "${option}" ]; then param= ; fi
	if [ -n "${param}" ]; then option=${option%=*} ; fi

	case ${option} in
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


umask 022
# VERIFICATION
if [[ ! ${name} =~ ^[A-Z,0-9]{4}[0-9]{2}[A-Z]{3}$ ]]; then
	echo "$(basename $0) FATAL ::: BAD INPUT NAME"
	echo ""
	print_usage
fi

# SETTING PARAMETERS & VARIABLES
SPOTGINS_DIR=.
if [[ -z $SPOTGINS_DIR ]]; then
        echo \$SPOTGINS_DIR is not defined
        echo This environment variable contains the path to the spotgins root folder
        exit 1
fi

### PATHS TO UPDATE ###
scratch_dir="/tmp"
listing_dir="${SPOTGINS_DIR}/listing/${name}"
file_ztd="${SPOTGINS_DIR}/series/SPOTGINS_${name}.ztd"
file_grad="${SPOTGINS_DIR}/series/SPOTGINS_${name}.grad"
sol_dir="result/ZIMM_20y"

#######################

stations_file="${SPOTGINS_DIR}/station/station_master_file.dat"

tropo_head=$(mktemp "${scratch_dir}/tropo_head".XXXX)
tropo_in=$(mktemp "${scratch_dir}/tropo_in".XXXX)
tropo_all=$(mktemp "${scratch_dir}/tropo_all".XXXX)
tropo_dates=$(mktemp "${scratch_dir}/tropo_dates".XXXX)
ztd_head=$(mktemp "${scratch_dir}/ztd_head".XXXX)
grad_head=$(mktemp "${scratch_dir}/grad_head".XXXX)
grad_body=$(mktemp "${scratch_dir}/grad_body".XXXX)
grad_out=$(mktemp "${scratch_dir}/grad_out".XXXX)
grad_out_tmp=$(mktemp "${scratch_dir}/grad_out_tmp".XXXX)
ztd_body=$(mktemp "${scratch_dir}/ztd_body".XXXX)
ztd_out=$(mktemp "${scratch_dir}/ztd_out".XXXX)

# SEARCH STATION IN MASTER FILE
station=$(grep " ${name} " ${stations_file})
if [[ ${#station} -eq 0 ]]; then
	echo "$(basename $0) FATAL ::: Need to add station to master file first !"
	echo ""
	print_usage
fi

Xref=$(echo ${station} | awk '{print $7}')
Yref=$(echo ${station} | awk '{print $8}')
Zref=$(echo ${station} | awk '{print $9}')
lon=$(echo ${station} | awk '{print $5}')
lat=$(echo ${station} | awk '{print $4}')
hei=$(echo ${station} | awk '{print $6}')
ac=$(echo ${station} | awk '{print $1}')

# EXTRACTING ESTIMATED TROPO
#> ${tropo_in}
# On recupere les noms des fichiers solutions pour eviter d'avoir des series tropo avec des ambiguites non fixees
#liste_sol=$(ls ${sol_dir}/*_${name}* | sed 's:.*/::' | sed 's/.\{5\}$//')
#listings=$(ls ${listing_dir}/*${name}_[0-9]*)
#echo "liste listings = ${listings}"
#listings=$(ls -t ${listing_dir}/*${name}* | awk -F '/' '
#{
#  filename = $NF
#  prefix = substr(filename, 1, 7)
#  if (!(prefix in seen)) {
#    seen[prefix] = $0
#    print $0
#  }
#}')

#listings=$(ls ${listing_dir}/*${name}* | grep -vF '.err' | rev | sed 's/\./ /' | rev | sort -k1,1 -k2,2r | awk '!seen[$1]++' | sed 's/ /\./')
listings=$(ls ${listing_dir}/*${name}* | grep -vF '.err' | awk -F. '{key=$1"."$2"."$3; date=$(NF-1); print key, date, $0}' | sort -k1,1 -k2,2r | awk '!seen[$1]++ {print $3}')

#echo "listings  = ${listings}"

while read listing; do
	#if [ $(ls ${listing_dir}/${line}* | wc -l) -ne 0 ];then
    #listing=$(ls ${listing_dir}/$line)
	#listing=$(echo ${listing_dir}/${line}*)
	#echo "listing=${listing}"	
	#[ -e "$listing" ] || continue

	#grep "^SINEX_TT2" $listing | tac | sort -u -k2,3 | awk '{for(i=4;i<=11;i++) $i*=1000; print}' > ${tropo_in} #Values in meters
	awk '/^SINEX_TT2/ {
		for(i=4;i<=11;i++) $i=sprintf("%.3f", $i*1000); 
        key=$2" "$3;
		count[key]++
        data[key]=$0    # écrase les anciennes occurrences
     }
     END {
        for (k in data)
			if (count[k] >= 2) #ne considere que le epoques qui apparaissent 2 fois: on ne sauve que les estimations avec amb fixee
				print data[k]
		
     }' "$listing" > "${tropo_in}"

	if [[ -s ${tropo_in} ]]; then
		tExe=$(echo $listing | rev | cut -c6-18 | rev)
		read tOffset version_gins pres_gps pres_gal version_prairie  <<< $(awk '
                BEGIN { tOffset="0"; version="UNKNOWN"; gps=0; gal=0; vprairie = "UNKNOWN"}
                /arc_start :/ && tOffset=="0" {
                    gsub(/\]/,"",$0)
                    split($0,a,",")
                    tOffset=a[2]
                }
                /gins90 est :/ && version=="UNKNOWN" {
                    n=split($0,a,".")
                    version=a[n]
                }
                /RAPH_GAL:CC/ { gal=1 }
                /RAPH_GPS:CC/ { gps=1 }
				/Prog is prairie/ { vprairie=$5 }
                END { print tOffset, version, gps, gal, vprairie }
                ' "$listing")

		#echo "version_gins = ${version_gins}"
		#echo "version_prairie = ${version_prairie}"
		#echo "gps = ${pres_gps}"
		#echo "gal = ${pres_gal}"

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

		awk -v tOffset="$tOffset" -v tExe="$tExe" -v version_gins="$version_gins" -v const="$const" -v version_prairie="$version_prairie" \
        '{print $0, tOffset, tExe, version_gins, version_prairie, const}' "$tropo_in" >> "${tropo_all}"

	fi
done < <(echo "$listings")

### HEADER ###
echo "# Creation 
#--------------------------------------
# STATION          : ${name}
# ANALYSIS_CENTRE  : ${ac}
# STRATEGY_SUMMARY : https://www.poleterresolide.fr/geodesy-plotter/#/solution/SPOTGINS   
# REF_FRAME        : IGS20
# PRODUCTS         : G20/GRG
# CONSTELLATION    : ${const_head}
# UNITS            : millimeters
# ELLIPSOID        : GRS80
#--------------------------------------
# X_pos            : ${Xref}
# Y_pos            : ${Yref}
# Z_pos            : ${Zref}
# Longitude        : ${lon}
# Latitude         : ${lat}
# Height           : ${hei}
#--------------------------------------" > ${tropo_head}
# EXTRACTING STATION INFO
if [[ ! -s $file_ztd ]]; then

	{
	 echo "# SPOTGINS SOLUTION [TROPOSPHERE_ZTD] v2"
	 cat ${tropo_head}
	 echo "#MJD          TROTOT    TRODRY    TROWET  STDWET yyyy-mm-ddTHH:MM:SS  DecimalYear   Const  Dateofexe      GinsVersion  PrairieVersion"
	} > ${ztd_head}

else
	awk '
		/^#/ {print > head; next}
		{print > body}
		' head="$ztd_head" body="$ztd_body" ${file_ztd}

	#grep    "^#" ${file_ztd} > ${ztd_head}
	#grep -v "^#" ${file_ztd} > ${ztd_body}

	const_head_ini=$(grep "# CONSTELLATION.*:" ${file_ztd} | awk -F: '{ print $2 }')
	const_head=$(echo "${const_head_ini}${const_head}" | grep -o . | sort -ru | tr -d '\n')

fi

if [[ ! -s $file_grad ]]; then
	{
	 echo "# SPOTGINS SOLUTION [TROPOSPHERE_GRAD] v2"
	 cat ${tropo_head}
	 echo "#MJD           TGNTOT  STDTGN  TGETOT STDTGE  yyyy-mm-ddTHH:MM:SS  DecimalYear   Const  Dateofexe      GinsVersion  PrairieVersion"
	} > ${grad_head}

else
	awk '
		/^#/ {print > head; next}
		{print > body}
		' head="$grad_head" body="$grad_body" ${file_grad}
	#grep    "^#" ${file_grad} > ${grad_head}
	#grep -v "^#" ${file_grad} > ${grad_body}
	#Gal=$(grep "# CONSTELLATION.*:" ${file_grad} | awk -F: '{ print $2 }' | grep E | wc -l)
	const_head_ini=$(grep "# CONSTELLATION.*:" ${file_grad} | awk -F: '{ print $2 }')
	const_head=$(echo "${const_head_ini}${const_head}" | grep -o . | sort -ru | tr -d '\n')
fi


# SETTING OUTPUT FORMAT
#echo "DEBUG tropo_all = |${tropo_all}|"
#ls -l "${tropo_all}"

if [[ -s ${tropo_all} ]]; then

	> "${tropo_dates}"
	> "${grad_out_tmp}"

	awk -v tropo_file="${tropo_dates}" -v grad_file="${grad_out_tmp}" '
	{
    # --- Extraction depuis champ 3 : 25:020:01818 ---
    split($3, a, ":")

    year = "20" a[1]
    doy  = a[2]
    sec  = a[3]

	leap = ( (year%4==0 && year%100!=0) || (year%400==0) )

	mdays[1]=31
	mdays[2]=28+leap
	mdays[3]=31
	mdays[4]=30
	mdays[5]=31
	mdays[6]=30
	mdays[7]=31
	mdays[8]=31
	mdays[9]=30
	mdays[10]=31
	mdays[11]=30
	mdays[12]=31

	d=doy
	for(m=1;m<=12;m++){
    	if(d<=mdays[m]){
        	day=d
        	month=m
        	break
    	}
    	d-=mdays[m]
	}

    tOffset = $12
    sec_GPST = sec - tOffset

    hour   = int(sec_GPST/3600)
    minute = int((sec_GPST-3600*hour)/60)
    second = sec_GPST-3600*hour-60*minute

	if (minute==0){
        minute = 30
        sec_GPST = sec_GPST + 1800
    }

    # nombre de jours dans l année
	DIY = ( (year%4==0 && year%100!=0) || year%400==0 ) ? 366 : 365

	# calcul dec_year
	dec_year = year + (doy-1+sec_GPST/86400)/DIY

	# calcul mjd
	mjd0 = 51544 + 365*(year-2000) \
       + int((year-1997)/4) \
       - int((year-1901)/100) \
       + int((year-1601)/400)
	mjd = mjd0 + (doy-1) + sec_GPST/86400

    line_out = sprintf("%11.5f %4d-%02d-%02dT%02d:%02d:%02d %12.7f",mjd,year,month,d,hour,minute,second,dec_year)

	print line_out >> tropo_file
	
	if (hour==6 || hour==18){
		minute=0
		sec_GPST = sec_GPST - 1800
		mjd = mjd0 + (doy-1) + sec_GPST/86400
		dec_year = year + (doy-1+sec_GPST/86400)/DIY


		line_out_grad = sprintf(" %10.5f  %7.3f  %6.3f %7.3f %6.3f  %4d-%02d-%02dT%02d:%02d:%02d  %12.7f  %5s  %13s  %-12s %-12s",mjd,$8,$9,$10,$11,year,month,d,hour,minute,second,dec_year,$16,$13,$14,$15)
		print line_out_grad >> grad_file
	}
	
	}
	' "${tropo_all}"


	paste ${tropo_dates} ${tropo_all} | awk '{ printf " %10.5f  %8.3f  %8.3f  %7.3f %6.3f %18s  %12.7f  %5s  %13s  %-12s %-12s\n",$1,$7,$9,$10,$8,$2,$3,$19,$16,$17,$18 }' | sort -u -k1,1 > ${ztd_out}
	grep -v '^$' ${grad_out_tmp} | sort -u -k1,1 > ${grad_out}
	
	# COMPILE SERIES
	if ! cmp -s ${ztd_body} ${ztd_out}; then
		#different files
		now_date=$(date -u "+Creation %Y-%m-%d at %H:%M:%S (UTC)")
		sed -i "s/^# Creation .*/# ${now_date}/" ${ztd_head}
		#if [[ $Gal ]]; then
		sed -i "s/^# CONSTELLATION.*/# CONSTELLATION    : ${const_head}/" ${ztd_head}
		#fi
		cat ${ztd_out} ${ztd_body} 2> /dev/null | sort -u -k1,1 >> ${ztd_head} #erase old values with new ones when common dates
		mv ${ztd_head} ${file_ztd}
	fi
	if ! cmp -s ${grad_body} ${grad_out}; then
		#different files
		now_date=$(date -u "+Creation %Y-%m-%d at %H:%M:%S (UTC)")
		sed -i "s/^# Creation .*/# ${now_date}/" ${grad_head}
		#if [[ $Gal -eq 1 ]]; then
		sed -i "s/^# CONSTELLATION.*/# CONSTELLATION    : ${const_head}/" ${grad_head}
		#fi
		cat ${grad_out} ${grad_body} 2> /dev/null | sort -u -k1,1 >> ${grad_head} #erase old values with new ones when common dates
		mv ${grad_head} ${file_grad}
	fi
else
	echo Pas de listing, pas de tropo
fi
rm -f ${tropo_head} ${tropo_in} ${tropo_all} ${tropo_dates} ${ztd_head} ${ztd_body} ${ztd_out} ${grad_head} ${grad_out} ${grad_body} ${grad_out_tmp}
