10) Email alert to me following the AWS billing

14) if a batch of photos are uploaded only one email is necessary and not multiple unique mails.

15) Make the menu of the gallery same as the one in dashboard (remove pricing)

21) Implement a progress bar when a photographer is uploading the images, PLEASE NO EMOJIS

---------------------


1) Implement the cookies pop up, it's already implemented in the index.html from 1459 lines. So implement the backend for it and do that for all pages. DO NOT DO IT DYNAMICALLY, DO IT PAGE BY PAGE.

2) change the twitter in "Share" photo or gallery to X; because it's no more twitter it's X now.

3) add a logout/sign in indpendent button on right, because you removed it. This button must be there only when mobile menu is hidden, once the screen size reduced, the button must disapear.

4) Add the possibility to add more than one client for a gallery, change all impacted pages, like gallery settings for example.

5) Show to the photographer, the approved photos from the client by adding a green border in the gallery page only (in the gallery for photographers ONLY) and not only a hover text when the cursor is on the image.

6) Show to the photographer and clients for that gallery (exclude all unsigned users and exclude all people looking at the gallery when the gallery is public), the favorite photos from the client by adding an svg heart icon like the existing one when an image is opened but this time in the gallery page i want to see only the text. And that for client gallery and also the photographer gallery ONLY.

7) Change the content of the legal notice and privacy policy page knowing all until know about the software. if needed here's the email: support@galerly.com

8) Show the share button and favorite button in the approved images because it's missing for them.

9) verify the email before account creation, add the password reset option

10) Email alert to me following the AWS billing

18) implement the storage follow up in MB

20) make sure that the images aren't to attack us, because images can contain scripts
complete the migration, check @backend and @js to fullfil the complete migration

16) why there's two different columns in the galerly-galleries table: allow_download and allow_downloads; what's the differences?

17) Add the expiration feature

3) add a logout/sign in indpendent button on right, because you removed it. This button must be there only when mobile menu is hidden, once the screen size reduced, the button must disapear.


11) manage notification preferences via settings for photographers to their clients

12) implement multilple emails type and alerts that the photographer can use to notify their clients

13) Any tokens expire after 7 days

19) Pattern Used by Most “Big Tech”
Web session auth

✔️ HttpOnly cookies
✔️ Secure flag
✔️ SameSite=Lax or Strict
✔️ Short-lived session + server-side state

API auth or mobile/integrations

✔️ OAuth2 tokens
✔️ Stored securely by backend/mobile OS, NOT web JS
✔️ Rotating refresh tokens
✔️ PKCE for browser apps