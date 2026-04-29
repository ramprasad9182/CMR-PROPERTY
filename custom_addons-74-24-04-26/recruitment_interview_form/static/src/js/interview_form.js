(function () {

/* =========================================================
   BASIC ELEMENTS
========================================================= */

const form = document.getElementById("interview_form");
const experienceType = document.getElementById("experience_type");

// helper: today date
const getTodayISO = () => new Date().toISOString().split("T")[0];

// helper: all professional rows
const getProfessionalRows = () => document.querySelectorAll(".professional-entry");


/* =========================================================
   EXPERIENCE TYPE TOGGLE (Fresher / Experienced)
========================================================= */

function toggleRequired(ids, enable){
ids.forEach(id=>{
const el=document.getElementById(id);
if(!el) return;

enable
? el.setAttribute("required","required")
: el.removeAttribute("required");
});
}

function toggleExperienceFields(){

const isFresher=!experienceType.value || experienceType.value==="fresher";

const experienceFields=document.getElementById("experience_fields");
const professionalSection=document.getElementById("professional_section");
const salaryFields=document.getElementById("salary_fields");

experienceFields.style.display=isFresher?"none":"block";
professionalSection.style.display=isFresher?"none":"block";
salaryFields.style.display=isFresher?"none":"block";

toggleRequired(
["total_experience_years","retail_experience_years","current_salary","expected_salary"],
!isFresher
);

/* =========================================================
   REQUIRE FIRST EMPLOYMENT IF EXPERIENCED
========================================================= */

const firstCompany = document.querySelector("input[name='company_name_0']");
const firstDesignation = document.querySelector("input[name='designation_0']");
const firstFrom = document.querySelector("input[name='from_date_0']");
const firstTo = document.querySelector("input[name='to_date_0']");

if(!isFresher){

if(firstCompany) firstCompany.setAttribute("required","required");
if(firstDesignation) firstDesignation.setAttribute("required","required");
if(firstFrom) firstFrom.setAttribute("required","required");
if(firstTo) firstTo.setAttribute("required","required");

}else{

if(firstCompany) firstCompany.removeAttribute("required");
if(firstDesignation) firstDesignation.removeAttribute("required");
if(firstFrom) firstFrom.removeAttribute("required");
if(firstTo) firstTo.removeAttribute("required");

}

}




/* =========================================================
   VALIDATION HELPERS
========================================================= */

function validateDateRange(fromName,toName,count,label){

let valid=true;

for(let i=0;i<count;i++){

const from=document.querySelector(`input[name="${fromName}_${i}"]`);
const to=document.querySelector(`input[name="${toName}_${i}"]`);

if(!from||!to) continue;

to.setCustomValidity("");

if(from.value && to.value){

const f=new Date(from.value);
const t=new Date(to.value);

if(t<f){
to.setCustomValidity(`${label} To Date cannot be earlier than From Date`);
valid=false;
}

}

}

return valid;

}

function validateProfessionalDates(){

const count=parseInt(document.getElementById("professional_count")?.value||0);
return validateDateRange("from_date","to_date",count,"Work");

}

function validateEducationDates(){

const count=parseInt(document.getElementById("education_count")?.value||0);
return validateDateRange("date_from","date_to",count,"Education");

}

function validateSalaryFields(){

const current=parseFloat(document.getElementById("current_salary")?.value||0);
const expectedField=document.getElementById("expected_salary");
const expected=parseFloat(expectedField?.value||0);

if(!expectedField) return true;

expectedField.setCustomValidity("");

if(current && expected && expected<current){

expectedField.setCustomValidity(
"Expected salary cannot be less than current salary."
);

return false;

}

return true;

}

/* =========================================================
   REFERENCE SECTION
========================================================= */

window.addReferenceEntry = function(){

    const section = document.getElementById("reference-details-section");

    const index = parseInt(
        document.getElementById("reference_count").value
    );

    const wrapper = document.createElement("div");
    wrapper.className = "row reference-entry mb-3";

    wrapper.innerHTML = `
        <div class="col-md-6">
            <label>Name</label>
            <input type="text"
                   name="ref_name_${index}"
                   class="form-control"
                   placeholder="Reference Name">
        </div>

        <div class="col-md-6">
            <label>Phone Number</label>
            <input type="text"
                   name="ref_phone_${index}"
                   class="form-control"
                   pattern="\\d{10}"
                   title="Enter a 10-digit number"
                   placeholder="Phone Number">
        </div>

        <div class="col-md-2 mt-4">
            <button type="button"
                    class="btn btn-outline-danger btn-sm remove-entry">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `;

    section.appendChild(wrapper);

    document.getElementById("reference_count").value = index + 1;
};

/* =========================================================
   EDUCATION SECTION
========================================================= */

window.addEducationEntry=function(){

const section=document.getElementById("education-details-section");
const index=parseInt(document.getElementById("education_count").value);

// create row
const wrapper=document.createElement("div");
wrapper.className="row education-entry mb-3";

wrapper.innerHTML=`

<div class="col-md-4">
<label>Education Level</label>
<select name="degree_${index}" class="form-select degree-select" required>
<option value="">Select Level</option>
<option value="ssc">SSC</option>
<option value="inter">Inter</option>
<option value="graduate">Graduate</option>
<option value="bachelor">Bachelor Degree</option>
<option value="masters">Masters Degree</option>
<option value="doctoral">Doctoral Degree</option>
</select>
</div>

<div class="col-md-4">
<label>From Date</label>
<input type="date" name="date_from_${index}" class="form-control">
</div>

<div class="col-md-4">
<label>To Date</label>
<input type="date" name="date_to_${index}" class="form-control">
</div>

<div class="col-md-4 mt-2">
<label>Year of Passing</label>
<input type="text"
name="year_of_passing_${index}"
class="form-control"
readonly>
</div>

<div class="col-md-2 mt-4">
<button type="button"
class="btn btn-outline-danger btn-sm remove-entry">
<i class="bi bi-trash"></i>
</button>
</div>
`;

section.appendChild(wrapper);

// increase counter
document.getElementById("education_count").value=index+1;

// disable already selected degrees
updateUsedDegrees();

};

function updateUsedDegrees(){

const selects=document.querySelectorAll('select[name^="degree_"]');

const values=[...selects]
.map(s=>s.value)
.filter(v=>v);

selects.forEach(select=>{
select.querySelectorAll("option").forEach(opt=>{

if(!opt.value) return;

opt.disabled=
values.includes(opt.value)
&& opt.value!==select.value;

});
});

}


/* =========================================================
   PROFESSIONAL EXPERIENCE SECTION
========================================================= */

function updateTillDateVisibility(){

const rows=getProfessionalRows();

rows.forEach((row,i)=>{

const checkbox=row.querySelector(".till_date");

if(!checkbox) return;

checkbox.closest(".col-md-4").style.display =
(i===rows.length-1) ? "block" : "none";

});

}

function toggleAddProfessionalButton(){

const btn=document.getElementById("add_professional_btn");

if(!btn) return;

btn.disabled=!!document.querySelector(".till_date:checked");

}

window.addProfessionalEntry=function(){

if(document.querySelector(".till_date:checked")){

alert("You cannot add another experience while 'Till Date' is selected.");
return;

}

const section=document.getElementById("professional_fields");
const index=parseInt(document.getElementById("professional_count").value);

const wrapper=document.createElement("div");

wrapper.className="row professional-entry mb-3";

wrapper.innerHTML=`

<div class="col-md-4">
<label>Company *</label>
<input type="text"
name="company_name_${index}"
class="form-control"
required>
</div>

<div class="col-md-4">
<label>Designation *</label>
<input type="text"
name="designation_${index}"
class="form-control"
required>
</div>

<div class="col-md-4">
<label>Years of Experience *</label>
<input type="text"
name="years_experience_${index}"
class="form-control"
readonly>
</div>

<div class="col-md-4 mt-2">
<label>From Date *</label>
<input type="date"
name="from_date_${index}"
class="form-control">
</div>

<div class="col-md-4 mt-2">
<label>To Date *</label>
<input type="date"
name="to_date_${index}"
class="form-control">
</div>

<div class="col-md-4 mt-4">
<input type="checkbox" class="till_date">
Till Date (Still Working)
</div>

<div class="col-md-2 mt-4">
<button type="button"
class="btn btn-outline-danger btn-sm remove-entry">
<i class="bi bi-trash"></i>
</button>
</div>

`;

section.appendChild(wrapper);

document.getElementById("professional_count").value=index+1;

updateTillDateVisibility();

}


/* =========================================================
   DELETE ROW
========================================================= */

document.addEventListener("click",function(e){

const btn=e.target.closest(".remove-entry");

if(!btn) return;

const row=btn.closest(
".education-entry,.professional-entry,.reference-entry"
);

if(!row) return;

row.remove();

updateTillDateVisibility();

const addBtn=document.getElementById("add_professional_btn");

if(addBtn) addBtn.disabled=false;

});


/* =========================================================
   EXPERIENCE CALCULATION
========================================================= */

function calculateExperience(){

getProfessionalRows().forEach(row=>{

const from=row.querySelector("input[name^='from_date']");
const to=row.querySelector("input[name^='to_date']");
const till=row.querySelector(".till_date");
const output=row.querySelector("input[name^='years_experience']");

if(!from?.value){

output.value="";
return;

}

const start=new Date(from.value);

const end=till?.checked
? new Date()
: new Date(to?.value);

if(!end || end<start){

output.value="";
return;

}

let years=end.getFullYear()-start.getFullYear();
let months=end.getMonth()-start.getMonth();
let days=end.getDate()-start.getDate();

if(days<0){months--;days+=30;}
if(months<0){years--;months+=12;}

const result=[];

if(years) result.push(`${years} year${years>1?"s":""}`);
if(months) result.push(`${months} month${months>1?"s":""}`);
if(days) result.push(`${days} day${days>1?"s":""}`);

output.value=result.join(" ") || "0 days";

});

}


/* =========================================================
   GLOBAL CHANGE HANDLER
========================================================= */

document.addEventListener("change",function(e){

const name=e.target.name;

/* education validation */

if(name?.startsWith("date_from_") ||
name?.startsWith("date_to_")){

validateEducationDates();

}

/* education year auto fill */

if(name?.startsWith("date_to_")){

const row=e.target.closest(".education-entry");

if(!row) return;

const yearField=row.querySelector(
"input[name^='year_of_passing']"
);

if(yearField && e.target.value){

yearField.value =
new Date(e.target.value).getFullYear();

}

}

/* professional date validation */

if(name?.startsWith("from_date_") ||
name?.startsWith("to_date_")){

validateProfessionalDates();

calculateExperience();

const row=e.target.closest(".professional-entry");

if(!row) return;

const toInput=row.querySelector("input[name^='to_date']");
const till=row.querySelector(".till_date");

if(toInput && till){

if(toInput.value===getTodayISO()){

till.checked=true;
toInput.readOnly=true;

}else{

till.checked=false;
toInput.readOnly=false;

}

toggleAddProfessionalButton();

}

}

/* till date checkbox */

if(e.target.classList.contains("till_date")){

const row=e.target.closest(".professional-entry");

const toInput=row?.querySelector("input[name^='to_date']");

if(e.target.checked){

toInput.value=getTodayISO();
toInput.readOnly=true;

}else{

toInput.value="";
toInput.readOnly=false;

}

toggleAddProfessionalButton();

calculateExperience();

}

});

/* =========================================================
   SALARY LIVE VALIDATION
========================================================= */

document.addEventListener("input", function(e){

if(e.target.id==="current_salary" || e.target.id==="expected_salary"){

validateSalaryFields();

}

});


/* =========================================================
   PHOTO PREVIEW
========================================================= */

const photoInput=document.getElementById("photo_file");
const photoPreview=document.getElementById("photo_preview");
const photoContainer=document.getElementById("photo_preview_container");
const photoRemoveBtn=document.getElementById("remove_photo_btn");

if(photoInput && photoPreview){

photoInput.addEventListener("change",function(){

const file=this.files[0];

if(!file) return;

if(!file.type.startsWith("image/")){

alert("Upload JPG or PNG image");

this.value="";
return;

}

const reader=new FileReader();

reader.onload=function(e){

photoPreview.src=e.target.result;

photoPreview.classList.remove("d-none");

if(photoContainer)
photoContainer.style.display="flex";

if(photoRemoveBtn)
photoRemoveBtn.classList.remove("d-none");

};

reader.readAsDataURL(file);

});

if(photoRemoveBtn){

photoRemoveBtn.addEventListener("click",function(){

photoInput.value="";
photoPreview.src="";
photoPreview.classList.add("d-none");

if(photoContainer)
photoContainer.style.display="none";

photoRemoveBtn.classList.add("d-none");

});

}

}


/* =========================================================
   RESUME PREVIEW
========================================================= */

const resumeInput=document.getElementById("resume_file");
const resumeLink=document.getElementById("resume_preview_link");
const resumeContainer=document.getElementById("resume_preview_container");
const resumeRemoveBtn=document.getElementById("remove_resume_btn");

if(resumeInput && resumeLink){

resumeInput.addEventListener("change",function(){

const file=this.files[0];

if(!file) return;

const allowed=[
"application/pdf",
"application/msword",
"application/vnd.openxmlformats-officedocument.wordprocessingml.document"
];

if(!allowed.includes(file.type)){

alert("Upload PDF / DOC / DOCX");

this.value="";
return;

}

const url=URL.createObjectURL(file);

resumeLink.href=url;

resumeLink.textContent="📄 View Uploaded Resume";

if(resumeContainer)
resumeContainer.style.display="flex";

if(resumeRemoveBtn)
resumeRemoveBtn.classList.remove("d-none");

});

if(resumeRemoveBtn){

resumeRemoveBtn.addEventListener("click",function(){

resumeInput.value="";

resumeLink.href="#";
resumeLink.textContent="";

if(resumeContainer)
resumeContainer.style.display="none";

resumeRemoveBtn.classList.add("d-none");

});

}

}


/* =========================================================
   AGE CALCULATION
========================================================= */

const dob=document.getElementById("dob");
const age=document.getElementById("age");

if(dob){

dob.addEventListener("change",function(){

const birth=new Date(dob.value);

const today=new Date();

let a=today.getFullYear()-birth.getFullYear();

if(today.getMonth()<birth.getMonth()
||
(today.getMonth()===birth.getMonth()
&& today.getDate()<birth.getDate()))

a--;

age.value=a>0 ? a : "";

});

}


/* =========================================================
   BUTTON BINDINGS
========================================================= */

document.getElementById("add_professional_btn")
?.addEventListener("click",window.addProfessionalEntry);

document.getElementById("add_education_btn")
?.addEventListener("click",window.addEducationEntry);

document.getElementById("add_reference_btn")
?.addEventListener("click",window.addReferenceEntry);

if(experienceType){

experienceType.addEventListener("change",toggleExperienceFields);

toggleExperienceFields();

}
/* =========================================================
   FORM SUBMIT VALIDATION
========================================================= */

if(form){

form.addEventListener("submit",function(e){

const validSalary = validateSalaryFields();

if(!validSalary){

e.preventDefault();

const invalid=form.querySelector("input:invalid");

if(invalid){
invalid.reportValidity();
}

}

});

}

})();






//
//(function () {
//
////     Initialize Select2 for preferred companies
////    $(document).ready(function () {
////        $('.js-company-multiselect').select2({
////            width: '100%',
////            placeholder: 'Select Preferred Companies'
////        });
////    });
//
//
//    const form = document.getElementById("interview_form");
//    const experienceType = document.getElementById("experience_type");
//
//    const toggleRequired = (ids, enable) => {
//        ids.forEach(id => {
//            const el = document.getElementById(id);
//            if (el) {
//                if (enable) {
//                    el.setAttribute("required", "required");
//                } else {
//                    el.removeAttribute("required");
//                }
//            }
//        });
//    };
//
//   function toggleExperienceFields() {
//        const isFresher = !experienceType.value || experienceType.value === "fresher";
//
//        const experienceFields = document.getElementById("experience_fields");
//        const professionalFields = document.getElementById("professional_section");
//        const salaryFields = document.getElementById("salary_fields");
//
//        // Show or hide fields
//        experienceFields.style.display = isFresher ? "none" : "block";
//        professionalFields.style.display = isFresher ? "none" : "block";
//        salaryFields.style.display = isFresher ? "none" : "block";
//
//        // Toggle required attribute
//        toggleRequired(
//            ["total_experience_years", "retail_experience_years", "current_salary", "expected_salary"],
//            !isFresher
//        );
// // no #
//        const proInputs = professionalFields.querySelectorAll("input");
//        proInputs.forEach(input => {
//            if (!isFresher) {
//                input.setAttribute("required", "required");
//                const tillInput = document.getElementById("till_date");
//
//                 console.log(tillInput)
//                 tillInput.removeAttribute("required");
//                 console.log('done remove......')
//
//            } else {
//                input.removeAttribute("required");
//            }
//        });
//   }
//
//
//    function validateDateRange(fromName, toName, count, label) {
//    let isValid = true;
//
//    for (let i = 0; i < count; i++) {
//        const from = document.querySelector(`input[name="${fromName}_${i}"]`);
//        const to = document.querySelector(`input[name="${toName}_${i}"]`);
//
//        // Always clear old error
//        if (to) to.setCustomValidity('');
//
//        if (from && to && from.value && to.value) {
//            const fromDate = new Date(from.value);
//            const toDate = new Date(to.value);
//
//            if (toDate < fromDate) {
//                to.setCustomValidity(`${label} To Date cannot be earlier than From Date`);
//                isValid = false;
//            }
//        }
//    }
//
//    return isValid;
//}
//
//
//    function validateProfessionalDates() {
//        const count = parseInt(document.getElementById('professional_count')?.value || '0');
//        return validateDateRange('from_date', 'to_date', count, "Work");
//    }
//
//    function validateEducationDates() {
//        const count = parseInt(document.getElementById('education_count')?.value || '0');
//        return validateDateRange('date_from', 'date_to', count, "Education");
//    }
//    function validateSalaryFields() {
//    const currentSalary = document.getElementById("current_salary");
//    const expectedSalary = document.getElementById("expected_salary");
//
//    if (!currentSalary || !expectedSalary) return true;
//
//    expectedSalary.setCustomValidity(""); // clear old error
//
//    const current = parseFloat(currentSalary.value || 0);
//    const expected = parseFloat(expectedSalary.value || 0);
//
//    if (current && expected && expected < current) {
//        expectedSalary.setCustomValidity(
//            "Expected salary cannot be less than current salary."
//        );
//        return false;
//    }
//    return true;
//}
//
//
//    window.addEducationEntry = function () {
//        const section = document.getElementById("education-details-section");
//        const index = parseInt(document.getElementById("education_count").value);
//
//        const wrapper = document.createElement("div");
//        wrapper.className = "row education-entry mb-3";
//        wrapper.innerHTML = `
//            <div class="col-md-4">
//                <label>Education Level</label>
//                <select name="degree_${index}" class="form-select degree-select" required>
//                    <option value="">Select Level</option>
//                    <option value="ssc">SSC</option>
//                    <option value="inter">Inter</option>
//                    <option value="graduate">Graduate</option>
//                    <option value="bachelor">Bachelor Degree</option>
//                    <option value="masters">Masters Degree</option>
//                    <option value="doctoral">Doctoral Degree</option>
//                </select>
//            </div>
//            <div class="col-md-4">
//                <label>From Date:</label>
//                <input type="date" name="date_from_${index}" class="form-control"/>
//            </div>
//            <div class="col-md-4">
//                <label>To Date:</label>
//                <input type="date" name="date_to_${index}" class="form-control"/>
//            </div>
//            <div class="col-md-4 mt-2">
//                <label>Year of Passing</label>
//                <input type="text" name="year_of_passing_${index}" class="form-control"/>
//            </div>
//            <div class="col-md-2 mt-4">
//                <button type="button" class="btn btn-outline-danger btn-sm remove-entry" title="Delete">
//                    <i class="bi bi-trash"></i>
//                </button>
//            </div>
//        `;
//        section.appendChild(wrapper);
//        document.getElementById("education_count").value = index + 1;
//
////        setupRealTimeDateValidation();
//        updateUsedDegrees(); // ✅ Important: Refresh disabled options
//    };
//
//    function updateUsedDegrees() {
//        const selectedValues = [];
//        const allSelects = document.querySelectorAll('select[name^="degree_"]');
//
//        // Step 1: Collect all selected values
//        allSelects.forEach(select => {
//            if (select.value) selectedValues.push(select.value);
//        });
//
//        // Step 2: For each dropdown, disable values selected elsewhere
//        allSelects.forEach(currentSelect => {
//            const currentValue = currentSelect.value;
//            const options = currentSelect.querySelectorAll('option');
//
//            options.forEach(option => {
//                if (option.value === "") {
//                    option.disabled = false;
//                    return;
//                }
//                // Disable if selected elsewhere and not the current value
//                if (selectedValues.includes(option.value) && option.value !== currentValue) {
//                    option.disabled = true;
//                } else {
//                    option.disabled = false;
//                }
//            });
//        });
//}
//
//
//   window.addProfessionalEntry = function () {
//    const section = document.getElementById('professional_fields');
//    const index = parseInt(document.getElementById('professional_count').value);
//
//    const wrapper = document.createElement('div');
//    wrapper.className = 'row professional-entry mb-3';
//
//    wrapper.innerHTML = `
//        <div class="col-md-4">
//            <label>Company <span style="color:red">*</span></label>
//            <input type="text" name="company_name_${index}" class="form-control" required/>
//        </div>
//
//        <div class="col-md-4">
//            <label>Designation <span style="color:red">*</span></label>
//            <input type="text" name="designation_${index}" class="form-control" required/>
//        </div>
//
//        <div class="col-md-4">
//            <label>Years of Experience <span style="color:red">*</span></label>
//            <input type="text"
//                   name="years_experience_${index}"
//                   class="form-control"
//                   readonly="readonly"/>
//        </div>
//
//        <div class="col-md-4 mt-2">
//            <label>From Date <span style="color:red">*</span></label>
//            <input type="date"
//                   name="from_date_${index}"
//                   class="form-control"/>
//        </div>
//
//        <div class="col-md-4 mt-2">
//            <label>To Date <span style="color:red">*</span></label>
//            <input type="date"
//                   name="to_date_${index}"
//                   class="form-control"/>
//        </div>
//
//        <div class="col-md-4 mt-4">
//            <input type="checkbox" class="till_date"/>
//            Till Date (Still Working)
//        </div>
//
//        <div class="col-md-2 mt-4">
//            <button type="button"
//                    class="btn btn-outline-danger btn-sm remove-entry">
//                <i class="bi bi-trash"></i>
//            </button>
//        </div>
//    `;
//
//    section.appendChild(wrapper);
//    document.getElementById('professional_count').value = index + 1;
//};
//
//
//    window.addReferenceEntry = function () {
//        const section = document.getElementById("reference-details-section");
//        const index = parseInt(document.getElementById("reference_count").value);
//
//        const wrapper = document.createElement("div");
//        wrapper.className = "row reference-entry mb-3";
//        wrapper.innerHTML = `
//            <div class="col-md-6">
//                <label>Name</label>
//                <input type="text" name="ref_name_${index}" class="form-control" required/>
//            </div>
//            <div class="col-md-6">
//                <label>Phone Number</label>
//                <input type="text" name="ref_phone_${index}" class="form-control" pattern="\\d{10}" required/>
//            </div>
//            <div class="col-md-2 mt-4">
//                <button type="button" class="btn btn-outline-danger btn-sm remove-entry" title="Delete">
//                    <i class="bi bi-trash"></i>
//                </button>
//            </div>
//        `;
//        section.appendChild(wrapper);
//        document.getElementById("reference_count").value = index + 1;
//    };
//
//    document.addEventListener("input", function (e) {
//    if (e.target.id === "current_salary" || e.target.id === "expected_salary") {
//        validateSalaryFields();
//    }
//});
//
//
//    document.addEventListener("click", function (e) {
//        const removeBtn = e.target.closest(".remove-entry");
//        if (removeBtn) {
//            const entry = removeBtn.closest(".education-entry, .professional-entry, .reference-entry");
//            if (entry) entry.remove();
//        }
//    });
//
//    if (form) {
//    form.addEventListener("submit", function (e) {
//        const validPro = validateProfessionalDates();
//        const validEdu = validateEducationDates();
//        const validSalary = validateSalaryFields();
//
//       if (!validPro || !validEdu || !validSalary) {
//    e.preventDefault();
//    const invalidFields = form.querySelectorAll("input:invalid, select:invalid");
//    if (invalidFields.length) {
//        invalidFields[0].reportValidity();
//    }
//}
//
//    });
//}
//    document.addEventListener("change", function (e) {
//    const name = e.target.name;
//
//    // For education degree dropdown
//    if (name?.startsWith("degree_")) {
//        updateUsedDegrees();
//    }
//
//    // Real-time professional date validation
//    if (name?.startsWith("from_date_") || name?.startsWith("to_date_")) {
//        validateProfessionalDates();
//    }
//
//    // Real-time education date validation
//    if (name?.startsWith("date_from_") || name?.startsWith("date_to_")) {
//        validateEducationDates();
//    }
//});
//document.addEventListener("change", function (e) {
//
//    // Handle Till Date for ALL rows (including Add More)
//    if (e.target.classList.contains("till_date")) {
//        const row = e.target.closest(".professional-entry");
//        if (!row) return;
//
//        const toDateInput = row.querySelector("input[name^='to_date']");
//        if (!toDateInput) return;
//
//        if (e.target.checked) {
//            toDateInput.value = getTodayISO();
//            toDateInput.removeAttribute("required");
//        } else {
//            toDateInput.value = "";
//            toDateInput.setAttribute("required", "required");
//        }
//    }
//
//    // Auto recalc experience for ALL rows
//    if (
//        e.target.matches("input[name^='from_date']") ||
//        e.target.matches("input[name^='to_date']") ||
//        e.target.classList.contains("till_date")
//    ) {
//        calculateExperience();
//    }
//});
//
//
//
//    document.getElementById("add_professional_btn")?.addEventListener("click", window.addProfessionalEntry);
//    document.getElementById("add_reference_btn")?.addEventListener("click", window.addReferenceEntry);
//    document.getElementById("add_education_btn")?.addEventListener("click", window.addEducationEntry);
//
//
//    function calculateAgeFromDOB() {
//        const dobField = document.getElementById("dob");
//        const ageField = document.getElementById("age");
//
//        if (dobField && ageField && dobField.value) {
//            const dob = new Date(dobField.value);
//            const today = new Date();
//            let age = today.getFullYear() - dob.getFullYear();
//            const m = today.getMonth() - dob.getMonth();
//
//            if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
//                age--;
//            }
//
//            ageField.value = age > 0 ? age : '';
//        } else if (ageField) {
//            ageField.value = '';
//        }
//    }
//
//    const dobInput = document.getElementById("dob");
//    if (dobInput) {
//        dobInput.addEventListener("change", calculateAgeFromDOB);
//        calculateAgeFromDOB(); // run once on load
//    }
//    function getTodayISO() {
//    const today = new Date();
//    return today.toISOString().split('T')[0]; // yyyy-mm-dd
//}
//
//    function calculateExperience() {
//    const rows = document.querySelectorAll(".professional-entry");
//
//    rows.forEach(row => {
//        const fromInput  = row.querySelector("input[name^='from_date']");
//        const toInput    = row.querySelector("input[name^='to_date']");
//        const tillInput  = row.querySelector(".till_date");
//        const yearsInput = row.querySelector("input[name^='years_experience']");
//
//        if (!fromInput || !fromInput.value) {
//            yearsInput.value = "";
//            return;
//        }
//
//        let fromDate = new Date(fromInput.value);
//        let toDate;
//
//        if (tillInput && tillInput.checked) {
//            toDate = new Date(); // today
//        } else if (toInput && toInput.value) {
//            toDate = new Date(toInput.value);
//        } else {
//            yearsInput.value = "";
//            return;
//        }
//
//        if (toDate < fromDate) {
//            yearsInput.value = "";
//            return;
//        }
//
//        let start = new Date(fromDate);
//        let end   = new Date(toDate);
//
//        let years = end.getFullYear() - start.getFullYear();
//        let months = end.getMonth() - start.getMonth();
//        let days = end.getDate() - start.getDate();
//
//        if (days < 0) {
//            months--;
//            const prevMonth = new Date(end.getFullYear(), end.getMonth(), 0);
//            days += prevMonth.getDate();
//        }
//
//        if (months < 0) {
//            years--;
//            months += 12;
//        }
//
//        // Build readable text
//        let result = [];
//        if (years > 0) result.push(`${years} year${years > 1 ? 's' : ''}`);
//        if (months > 0) result.push(`${months} month${months > 1 ? 's' : ''}`);
//        if (days > 0) result.push(`${days} day${days > 1 ? 's' : ''}`);
//
//        yearsInput.value = result.length ? result.join(' ') : "0 days";
//    });
//}
//
//
//
//
//
//// attach listener for all date/till-date changes
//document.addEventListener("change", e => {
//    if (e.target.matches("input[name^='from_date'], input[name^='to_date'], .till_date")) {
//        calculateExperience();
//    }
//});
//document.addEventListener("change", function (e) {
//    if (e.target.classList.contains("till_date")) {
//        const row = e.target.closest(".professional-entry");
//        if (!row) return;
//
//        const toDateInput = row.querySelector("input[name^='to_date']");
//
//        if (!toDateInput) return;
//
//        if (e.target.checked) {
//            // ✅ If Till Date checked → set today
//            toDateInput.value = getTodayISO();
//            toDateInput.removeAttribute("required");
//        } else {
//            // ❌ If unchecked → clear To Date
//            toDateInput.value = "";
//            toDateInput.setAttribute("required", "required");
//        }
//
//        // 🔄 Recalculate experience
//        calculateExperience();
//
//    }
//});
//
//
//// ===============================
//// EDUCATION: Auto-fill Year of Passing from To Date
//// ===============================
//document.addEventListener("change", function (e) {
//    if (e.target.name && e.target.name.startsWith("date_to_")) {
//        const row = e.target.closest(".education-entry");
//        if (!row || !e.target.value) return;
//
//        const yearInput = row.querySelector("input[name^='year_of_passing']");
//        if (!yearInput) return;
//
//        const year = new Date(e.target.value).getFullYear();
//        yearInput.value = year;
//    }
//});
//
//
////  function experience_count() {
////    const rows = document.querySelectorAll(".professional-entry");
////    console.log("🔍 Found rows:", rows.length);
////
////    // If no dynamic rows exist, fall back to single row with IDs
////    if (rows.length === 1) {
////        console.log("⚠️ No .professional-entry rows found → using fallback IDs");
////
////        const fromDateInput = document.getElementById('from_date_0');
////        const toDateInput   = document.getElementById('to_date_0');
////        const yearsInput    = document.getElementById('years_experience_0');
////
////        console.log("Fallback Inputs:", { fromDateInput, toDateInput, yearsInput });
////
////        if (fromDateInput && toDateInput && yearsInput) {
////            calculateYears(fromDateInput, toDateInput, yearsInput, "Fallback Row");
////        } else {
////            console.log("⚠️ Fallback inputs not found");
////        }
////
////    }
////
////    // If multiple rows exist
////    rows.forEach((row, index) => {
////        console.log(`➡️ Checking row ${index + 1}`);
////        console.log(rows,"..........");
////        console.log(index,"///////////");
////        console.log(row.querySelector(".from_date_0"));
////        const fromDateInput = row.querySelectorAll(".from_date_0");
////        const toDateInput   = row.querySelectorAll(".to_date_0");
////        const yearsInput    = row.querySelectorAll(".years_experience");
////
////        console.log("Row inputs:", { fromDateInput, toDateInput, yearsInput });
////        console.log(fromDateInput.value);
////
////        if (fromDateInput && toDateInput && yearsInput) {
////            calculateYears(fromDateInput, toDateInput, yearsInput, `Row ${index + 1}`);
////        } else {
////            console.log(`⚠️ Missing input(s) in Row ${index + 1}`);
////        }
////    });
////}
////
////// 🔑 Helper function
////function calculateYears(fromDateInput, toDateInput, yearsInput, label = "") {
////    const fromDate = new Date(fromDateInput.value);
////    const toDate   = new Date(toDateInput.value);
////    console.log('from',fromDate,'to',toDate)
////
////    console.log(`📅 ${label}: From = ${fromDateInput.value}, To = ${toDateInput.value}`);
////
////    if (fromDateInput.value && toDateInput.value && !isNaN(fromDate) && !isNaN(toDate)) {
////        let months = (toDate.getFullYear() - fromDate.getFullYear()) * 12;
////        months += (toDate.getMonth() - fromDate.getMonth());
////        let years = Math.max(0, months / 12);
////        yearsInput.value = years.toFixed(1);
////
////        console.log(`✅ ${label}: Calculated Years = ${years.toFixed(1)}`);
////    } else {
////        yearsInput.value = "";
////        console.log(`⚠️ ${label}: Dates invalid or missing → clearing value`);
////    }
////}
////
////// --- Attach listeners directly ---
////const from_exp = document.querySelectorAll('.from_date_0');  // use # for ID
////const to_exp   = document.querySelectorAll('.to_date_0');    // same here
////
////if (from_exp.length > 0 && to_exp.length > 0) {
////    from_exp.forEach(input => {
////        input.addEventListener('change', experience_count);
////    });
////    to_exp.forEach(input => {
////        input.addEventListener('change', experience_count);
////    });
////    console.log("✅ Attached listeners for fallback single-row inputs");
////} else {
////    console.log("⚠️ Fallback single-row inputs not found");
////}
////
////
////// For dynamically added rows (event delegation)
////document.addEventListener('change', e => {
////    if (e.target.classList.contains("to_date_0") || e.target.classList.contains("from_date_0")) {
////        console.log("🔔 Change detected → Recalculating experience");
////        experience_count();
////    }
////});
////
////// Run once immediately
////experience_count();
//
//
//    if (experienceType) {
//        experienceType.addEventListener("change", toggleExperienceFields);
//        toggleExperienceFields();
//    }
//
////    setupRealTimeDateValidation();
//// === Photo Upload with Validation & Remove ===
//const photoInput = document.getElementById('photo_file');
//const photoPreview = document.getElementById('photo_preview');
//const photoContainer = document.getElementById('photo_preview_container');
//const photoRemoveBtn = document.getElementById('remove_photo_btn');
//
//if (photoInput && photoPreview && photoContainer && photoRemoveBtn) {
//  photoInput.addEventListener('change', function (e) {
//    const file = e.target.files[0];
//    if (file) {
//      if (!file.type.startsWith('image/')) {
//        alert('Please upload a valid image file (PNG, JPG, JPEG)');
//        photoInput.value = "";
//        photoPreview.src = "";
//        photoContainer.style.display = 'none';
//        photoRemoveBtn.classList.add('d-none');
//        photoInput.setAttribute('required', 'required');
//        return;
//      }
//
//      const reader = new FileReader();
//      reader.onload = function (event) {
//        photoPreview.src = event.target.result;
//        photoPreview.classList.remove('d-none');
//        photoContainer.style.display = 'flex';
//        photoRemoveBtn.classList.remove('d-none');
//        photoInput.removeAttribute('required');
//      };
//      reader.readAsDataURL(file);
//    }
//  });
//
//  photoRemoveBtn.addEventListener('click', function () {
//    photoInput.value = "";
//    photoPreview.src = "";
//    photoPreview.classList.add('d-none');
//    photoContainer.style.display = 'none';
//    photoRemoveBtn.classList.add('d-none');
//    photoInput.setAttribute('required', 'required');
//  });
//}
//
//// === Resume Upload with Validation & Remove ===
//const resumeInput = document.getElementById('resume_file');
//const resumeLink = document.getElementById('resume_preview_link');
//const resumeContainer = document.getElementById('resume_preview_container');
//const resumeRemoveBtn = document.getElementById('remove_resume_btn');
//
//if (resumeInput && resumeLink && resumeContainer && resumeRemoveBtn) {
//  resumeInput.addEventListener('change', function (e) {
//    const file = e.target.files[0];
//    const allowedTypes = [
//      'application/pdf',
//      'application/msword',
//      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
//    ];
//
//    if (file) {
//      if (!allowedTypes.includes(file.type)) {
//        alert('Please upload a valid resume file (PDF, DOC, DOCX)');
//        resumeInput.value = "";
//        resumeLink.href = "#";
//        resumeLink.textContent = "";
//        resumeContainer.style.display = 'none';
//        resumeRemoveBtn.classList.add('d-none');
//        resumeInput.setAttribute('required', 'required');
//        return;
//      }
//
//      const url = URL.createObjectURL(file);
//      resumeLink.href = url;
//      resumeLink.textContent = "📄 View Uploaded Resume";
//      resumeContainer.style.display = 'flex';
//      resumeRemoveBtn.classList.remove('d-none');
//      resumeInput.removeAttribute('required');
//    }
//  });
//
//  resumeRemoveBtn.addEventListener('click', function () {
//    resumeInput.value = "";
//    resumeLink.href = "#";
//    resumeLink.textContent = "";
//    resumeContainer.style.display = 'none';
//    resumeRemoveBtn.classList.add('d-none');
//    resumeInput.setAttribute('required', 'required');
//  });
//}
///* ============================================================
//   ADDITIONAL TILL DATE FUNCTIONALITY (DO NOT MODIFY EXISTING)
//============================================================ */
//
//function toggleAddProfessionalButton() {
//    const addBtn = document.getElementById("add_professional_btn");
//    if (!addBtn) return;
//
//    const hasCurrent = document.querySelector(".till_date:checked");
//    addBtn.disabled = !!hasCurrent;
//}
//
//// Handle all Till Date + To Date sync
//document.addEventListener("change", function (e) {
//
//    // 1️⃣ Tick Till Date → To Date auto today
//    if (e.target.classList.contains("till_date")) {
//
//        const row = e.target.closest(".professional-entry");
//        if (!row) return;
//
//        const toInput = row.querySelector("input[name^='to_date']");
//        if (!toInput) return;
//
//        if (e.target.checked) {
//            toInput.value = getTodayISO();
//            toInput.readOnly = true;
//        } else {
//            toInput.value = "";
//            toInput.readOnly = false;
//        }
//
//        toggleAddProfessionalButton();
//    }
//
//    // Enter today manually → Till Date auto checked
//    if (e.target.name && e.target.name.startsWith("to_date_")) {
//
//        const row = e.target.closest(".professional-entry");
//        if (!row) return;
//
//        const tillCheckbox = row.querySelector(".till_date");
//        if (!tillCheckbox) return;
//
//        if (e.target.value === getTodayISO()) {
//            tillCheckbox.checked = true;
//            e.target.readOnly = true;
//        } else {
//            tillCheckbox.checked = false;
//            e.target.readOnly = false;
//        }
//
//        toggleAddProfessionalButton();
//    }
//});
//
//// Try adding → Alert shown
//const originalAddProfessionalEntry = window.addProfessionalEntry;
//
//window.addProfessionalEntry = function () {
//
//    if (document.querySelector(".till_date:checked")) {
//        alert("You cannot add another experience while 'Till Date' is selected.");
//        return;
//    }
//
//    originalAddProfessionalEntry();
//};
//
//})();
