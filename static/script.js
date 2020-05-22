window.onload = () => 
{
    date_selector();
    totals_selector();
}

function totals_selector()
{
    let totals_selector = document.getElementById("totals-selector");
    let totals = document.getElementById("totals").getElementsByTagName('div');
    
    update_totals();
    totals_selector.onchange = () => update_totals();

    function update_totals()
    {
        for(let i = 0; i < totals.length; i++)
        {
            totals[i].hidden = true;
        }
    
        totals[totals_selector.value].hidden = false;
    }
}

function date_selector()
{
    today = new Date();

    let months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    let days = get_array_range(1, 31);
    let years = get_array_range(today.getFullYear(), today.getFullYear() + 10);

    let months_selector = document.getElementById("months_selector");
    let days_selector = document.getElementById("days_selector");
    let years_selector = document.getElementById("years_selector");

    for (let i = 0; i < days.length; i++)
    {
        let opt = document.createElement("option");
        opt.value = days[i];
        opt.textContent = days[i];
        days_selector.appendChild(opt);
    }

    for (let i = 0; i < years.length; i++)
    {
        let opt = document.createElement("option");
        opt.value = years[i];
        opt.textContent = years[i];
        years_selector.appendChild(opt);
    }

    for (let i = 0; i < months.length; i++)
    {
        let opt = document.createElement("option");
        opt.value = i + 1; // gets the month as a number
        opt.textContent = months[i];
        months_selector.appendChild(opt);
    }

    months_selector.getElementsByTagName("option")[today.getMonth()].selected = 'selected';
}

function get_array_range(start, end)
{
    let arr = [];
    for (let i = start; i < end+1; i++)
        arr.push(i);
    return arr;
}


