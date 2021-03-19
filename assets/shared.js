/* Shared JS functions across pages in the chase applet */
/* jQuery must be loaded first */

function loadPlacefileLinks(api_base) {
    // Note: these are considered static, so just set the team-dependent ones
    var chase_base_url = "https://chase.iawx.info/";
    var team_id = localStorage.getItem("team_id");

    $("#team-current").val(chase_base_url + api_base + "placefile/" + team_id + "/current/content");
    $("#team-tracks").val(chase_base_url + api_base + "placefile/" + team_id + "/tracks/content");
    $("#team-history").val(chase_base_url + api_base + "placefile/" + team_id + "/history/content");
}
