# Exam Center Randomization script

The goal of this script is to assign exam centers to students.

## Steps

1. Prepare input files in specified format
2. Run program and re run if -
   - Any school has students that have not been assigned a center.
   - Distribution across centers is uneven
3. Perform sanity check of distributed centers
4. Manually reassign impractical centers and odd lot allocations. Keep changes to minimum.

## Allocation Guidelines

- हरेक विद्यालयमा परिक्षार्थीको संख्या र परीक्षा केन्द्रको सिट संख्या लिने
- हरेक विद्यालय र केन्द्रको गुगल म्यापबाट latitude, longitude निकाली दुरी निकाल्ने आधारको रुपमा प्रयोग गर्ने
- विद्यालयबाट नजिक पर्ने केन्द्रलाई प्राथमिकता दिनुपर्ने
- एक विद्यालयको परिक्षार्थी संख्या हेरी सकभर १००, २०० भन्दा बढी परीक्षार्थी एकै केन्द्रमा नपर्ने गरी बाँढ्न पर्ने
- आफ्नै विद्यालयमा केन्द्र पार्न नहुने
- दुई विद्यालयका परीक्षार्थीको केन्द्र एक अर्कामा पर्न नहुने, अर्थात् कुनै विद्यालयका परीक्षार्थीको केन्द्र परेको विद्यालयका परीक्षार्थीहरूको केन्द्र अघिल्लो विद्यालयमा पार्न नहुने ।
- एकै स्वामित्व / व्यवस्थापनको भनी पहिचान भएका केन्द्रमा पार्न नहुने
- विगतमा कुनै विद्यालयको कुनै केन्द्रमा पार्दा समस्या देखिएकोमा केन्द्र नदोहोऱ्याउन नहुने
- प्रत्येक पटक केन्द्र तोक्ने प्रोग्राम चलाउदा फरक फरक नतिजा आउने गरी ऱ्यान्डमाइज भएको हुनु पर्ने

## Parameters

PREF_DISTANCE_THRESHOLD = 2 # Preferred threshold distance in kilometers, centers should be within this distance from school if possible

ABS_DISTANCE_THRESHOLD = 7 # Absolute threshold distance in kilometers

MIN_STUDENT_IN_CENTER = 10 # minimum number of students from a school to be assigned to a center under normal circumstances

STRETCH_CAPACITY_FACTOR = 0.02 # how much can center capacity be stretched if need arises

PREF_CUTOFF = -4 # Do not allocate students with pref score less than cutoff

## Input files

Files should be tab delimited

### school.tsv

One entry per school.

    scode count name-address lat long
    27101 1776 काठमाण्डौ मोडेल मा.वि., वागवजार 27.7067463495 85.3188922809
    27007 1700 ट्रिनीटी इन्टरनेशनल मा.वि., डिल्लीबजार 27.7038931952 85.3251961353
    27045 1278 साउथ वेस्टर्न स्टेट मा.वि., बसुन्धारा 27.7396600173 85.3254532539
    27127 1210 क्यापिटल मा.वि., कोटेश्वर 27.673541693 85.3449013829

### centers.tsv

One entry per center. cscode should match scode

    cscode capacity name address नाम ठेगाना lat long
    27003 500 NATIONAL SCHOOL OF SCIENCES SECONDARY SCHOOL LAINCHAUR नेशनल स्कुल अफ साइन्सेस मा.वि लैनचौर 27.71933026 85.31413793
    27051 500 UNIGLOBE MA VI KAMALADI युनिग्लोब मा.वि कमलादी 27.70792875 85.32068522
    27045 568 SOUTH WESTERN ACADEMY SECONDARY SCHOOL BASUNDHARA साउथ वेर्ष्टन एकेडेमी मा.वि. बसुन्धरा 27.74212647 85.33392421

### prefs.tsv

Prioritize or deprioritize school and center pair. -ve pref score depriotizes. if pref score is less than `PREF_CUTOFF` center will be excluded from consideration

    scode cscode pref reason
    27xxx 27yyy -5 same management
    27yyy 27xxx -5 same management
    27aaa 27bbb -1  last year's center

## Output

Console output contains information about center allocation run.

    remaining capacity at center (-ve if stretched capacity is used)
       |
    (-11, '27022'), (-11, '27045'), (-11, '27057')
             |
        center code

    Total remaining capacity across all centers: 190
    Students not assigned: 29
