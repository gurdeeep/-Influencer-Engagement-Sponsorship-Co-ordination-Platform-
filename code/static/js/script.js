function showSelected(){
    const sponsor_search={"Select Search Type":"Select Search Type","ByName":"By Name","ByIndustry":"By Industry","ByBudget":"By Budget"}
   const influencer_search={"Select Search Type":"Select Search Type","ByName":"By Name","ByCategory":"By Category"},{"ByNiche":"By Niche"}
    const  campaign_search={"Select Search Type":"Select Search Type","ByName":"By Name","ByDescription":"By Description","ByVisibility":"By Visibility","ByGoals":"By Goals"}
     const adrequest_search={"Select Search Type":"Select Search Type","ByMessage":"By Message","ByRequirements":"ByRequirements","ByStatus":"By Status"}

    const selval=document.getElementById('searchtype').value;
    const subType = document.getElementById("subtype");
    const data;
    if(selval=='Sponsor'){
        data=sponsor_search;
    };
    if (selval=='Influencer') {
        data=influencer_search;
    };
    if (selval=='Campaign') {
        data=campaign_search;
    };
    if (selval=='AdRequest') {
        data=adrequest_search;
    };
    for (a in subType.options) { 
        subType.options.remove(0);
    }
    for (let key in data) {
      let option = document.createElement("option");
      option.setAttribute('value', key);

      let optionText = document.createTextNodedata[key]);
      option.appendChild(optionText);
      subType.appendChild(option);
}
