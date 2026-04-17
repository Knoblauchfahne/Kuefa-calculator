const fs=require('fs');
const data=JSON.parse(fs.readFileSync('standardbackup.json','utf8'));

const tr={
'Chana Masala':{
  z:'1. Soak the chickpeas overnight and cook in the morning. Dice the vegetables - the shape does not matter much as everything will be blended. Make a paste from peeled garlic and ginger with oil and salt.\n2. Mix the spices. Toast two-thirds of them in hot oil in the pot. Add the onions and the ginger-garlic paste and saute until translucent. Add the tomatoes and let simmer. Blend everything once cooked through.\n4. Add the chickpeas and remaining spices and bring to a boil again. Chop fresh coriander and serve on the side.',
  h:'Serve without a separate side - typically with basmati rice.\nThe sauce can also be thickened with chickpea water (aquafaba).',
  a:''},
'Chili':{
  z:'1. Soak the beans in water for at least 12 hours and pre-cook.\n2. Dice the vegetables and fry (add garlic last). Prepare the side dish in parallel.\n3. Add the spices and let them toast briefly in the pot before adding the beans and tomatoes.\n4. Simmer and add water if needed. Season to taste.',
  h:'Optional spices: bay leaves, oregano, sugar',
  a:''},
'Couscous-Pfanne':{
  z:'1. Bring vegetable stock to a boil and pour over the couscous. Cover and leave to swell for 5 minutes, then fluff with a fork.\n2. Saute onions and garlic in olive oil.\n3. Add courgette and peppers and fry for 5 minutes.\n4. Add chickpeas, tomatoes, cumin and turmeric and fry for 3 minutes.\n5. Fold in the couscous and season with lemon juice, salt and pepper.',
  h:'Couscous only needs hot water and no cooking time at all - ideal when fuel is scarce. Can also be served cold as a salad.',
  a:''},
'Kartoffelgulasch':{
  z:'1. Saute onions and garlic in olive oil until translucent.\n2. Stir in tomato paste and let it caramelise briefly.\n3. Add sweet and smoked paprika powder and caraway, toast briefly.\n4. Add the pepper pieces and fry for 3 minutes.\n5. Add the diced potatoes, pour over the crushed tomatoes and vegetable stock.\n6. Simmer for approx. 25-30 minutes until the potatoes are cooked through.\n7. Season with salt and pepper. For a thicker consistency, crush a few potatoes.',
  h:'Gets even better the next day! Keeps well in large pots on low heat. Optionally serve with bread.',
  a:''},
'Krautsalat':{
  z:'1. Shred the white cabbage into fine strips (a mandoline slicer is recommended for large quantities).\n2. Coarsely grate the carrots and add to the cabbage.\n3. Mix a dressing from vinegar, oil, sugar, salt and pepper.\n4. Pour the dressing over the salad and knead vigorously so the cabbage softens.\n5. Leave to marinate for at least 30 minutes - 2-3 hours is better.',
  h:'Preparing the day before is ideal! The salad improves as it marinates and takes up less volume. For large quantities, shred the cabbage with a bread slicer or mandoline.',
  a:''},
'Linsen-Dal':{
  z:'',
  h:'Red lentils do not need soaking. For large quantities, use a little more water as the lentils absorb a lot of liquid. Keeps well in a pot on low heat.',
  a:''},
'Overnight Oats':{
  z:'Soak the oats overnight in a closed container. In the morning, slice some apples or other fruit (optional) and serve on the side.',
  h:'There will always be people who want a version without sugar or without cinnamon.',
  a:''},
'Pad Thai mit Tofu':{
  z:'1. Soak the rice noodles: bring a pot of water to a boil, then remove from the heat. Soak the noodles for 4-7 minutes until they turn translucent white. They should be pliable but not soft. Drain, rinse under cold running water and drain thoroughly. Set aside.\n\n2. Mix chickpea flour, salt and 0.03 l water until lump-free. Heat a little oil in a wok or deep pan. Fry the chickpea mixture over medium-high heat for about 2 minutes, then stir with a spatula and cook for another 5-6 minutes until the mixture starts to set. Break up any large lumps. Set aside.\n\n3. Pad Thai sauce: whisk together tamarind paste, soy sauce, sugar, lime juice and sriracha.\n\n4. Wipe out the wok and heat again over medium heat. Fry garlic and shallots for 4-5 minutes until soft. Stir in the vegetables, Pad Thai sauce and tofu. Add the noodles; if still too firm, add about 0.015 l of water. Stir-fry for 3-4 minutes until noodles and vegetables are cooked but still have a bite.\n\n5. Garnish with peanuts, lime wedges, a handful of bean sprouts and some chopped coriander.',
  h:'For those with more time: soak the noodles in cold water for 40-60 minutes until white, soft and pliable but still with a bite. Drain well. Use immediately or store in a plastic bag in the fridge for up to 2 days.\nTip: soy sauce can be replaced with tamari (gluten-free).',
  a:''},
'Pasta Bolognese':{
  z:'1. Soak the soy mince in hot water for 10 minutes, then drain well.\n2. Saute onions, garlic and carrots in olive oil.\n3. Add the soy mince and fry briefly.\n4. Stir in the tomato paste and let it caramelise.\n5. Add the crushed tomatoes and season with oregano, basil, sugar, salt and pepper.\n6. Simmer over medium heat for about 20 minutes, stirring occasionally.\n7. Cook the pasta al dente in a separate pot of salted water.\n8. Season the sauce and serve with the pasta.',
  h:'Soy mince absorbs the flavour of the sauce well. Alternatively, green or brown lentils can be used as a meat substitute - they just need a little longer. For large quantities, cook the pasta in batches.',
  a:''},
'Rattatuille':{
  z:'1. Dice all vegetables into approx. 1x1 to 2x2 cm cubes.\n2. Add the diced vegetables with salt and oil to a preheated pot and fry until they develop some colour.\n3. Stir in tomato paste and deglaze with vinegar after a short time.\n4. Add the passata and spices and simmer until the desired consistency is reached.',
  h:'Often also made with sugar, bay leaves or allspice.',
  a:''},
'Soja Gyros':{
  z:'1. Briefly boil the water, soy chunks, soy sauce and vegetable stock powder together. Let the chunks absorb the liquid.\n\n2. Meanwhile, mix a marinade paste from lemon juice, garlic, oil, paprika powder, cumin and salt.\n\n3. Let the chunks cool. Mix with the paste, oregano and marjoram. Add the remaining oil.\n\n4. Leave everything to marinate thoroughly.\n\n5. Fry over high heat just before serving.',
  h:'Serve complete with potatoes, tzatziki and coleslaw.',
  a:''},
'Zitronen Risotto':{
  z:'1. Dice the vegetables and saute the onions in oil until translucent. Then add the garlic.\n2. Sweat the rice and toast for 1-2 minutes; optionally deglaze with white wine.\n3. Gradually stir in the stock. After 20 minutes, add the lemon juice.\n4. Season with salt, pepper, nutritional yeast and herbs.',
  h:'Do not add all the stock at once - stir frequently.',
  a:''},
'Rote Bete Salat Beilage':{
  z:'1. Slice the beetroot, apples (optional) and onions (optional). Briefly soak the onions in water.\n2. Make a dressing with lemon juice, oil, salt, pepper and optionally sugar.\n3. Leave to marinate for at least 10 minutes and fold in the herbs.',
  h:'Serve chilled.',
  a:''},
'Auberginenschnitzel mit Karottenpüree und Rosenkohl':{
  z:'1. Peel and dice the potatoes and carrots. Cover both with water in a pot and bring to a boil. For the Brussels sprouts, trim the stalks, remove outer leaves if necessary and halve. Bring a separate pot of water to a boil and cook the Brussels sprouts for 3-4 minutes (adding sugar or lemon juice to the water reduces bitterness). The cooking water may optionally be reused for the potatoes.\n2. Slice the aubergines into 1 cm thick rounds, salt and leave to draw out moisture, then pat dry. Meanwhile, prepare the breading station.\n2.1 Prepare a wet batter from flour, plant milk, oil, salt and optionally paprika powder. Set out breadcrumbs as the second station and have several GN trays ready to store the breaded slices.\n2.2 Dip the aubergine slices first into the wet batter, then into the breadcrumbs. Optionally store between layers of kitchen paper in GN trays.\n3. Fry the pre-cooked Brussels sprouts in a paella pan with oil until well browned, then season with salt and pepper.\n4. Mash or puree the cooked potatoes and carrots with vegan butter (or oil) and plant milk. Season with salt and pepper.\n5. Fill a paella pan with approx. 2-4 cm of oil for frying. Once the oil has reached temperature, fry the aubergine slices and store in shallow GN trays or transfer directly for serving.\n6. Optionally offer pomegranate seeds or herbs.',
  h:'',
  a:''},
'Sojagulasch':{
  z:'Best prepared the day before to allow the flavours to develop.\n1. Caramelise the onions; once cooked through, add the pepper paste and toast briefly.\n2. Deglaze with dark beer and reduce, then add caraway, allspice and bay leaves.\n3. Pour in half the stock and stir in the soy chunks. Stir well and leave to marinate overnight.\nOn the day of cooking:\n1. Dice the peppers into bite-sized pieces and sear. At the same time, heat up the goulash base from the day before and add the peppers.\n2. Bring the mixture to the desired consistency with the remaining stock and season to taste.',
  h:'',
  a:''},
'Spatzlebeilage':{
  z:'1. First mix all the dry ingredients, then add all the wet ingredients.\n2. Beat the batter with a wooden spoon until it forms bubbles.\n3. Leave to rest for 15-60 minutes.\n4. Press through a Spaetzle slicer or perforated GN tray into a pot of boiling water, then rinse with cold water.',
  h:'Exactly 5 kg of Spaetzle flour fits into a standard white tub, yielding a corresponding amount of Spaetzle.',
  a:''},
'Mildes Reis Gemüse':{
  z:'1. Cook the rice with twice the amount of water and prepare the vegetables. Use separate chopping boards.\n2. Steam or braise the vegetables with a little oil over low heat using a small amount of water.\n3. Mix the rice and vegetables and season to taste.',
  h:'',
  a:'Do not use iodised salt.'},
'Kartoffel-Gemüse-Pfanne':{
  z:'1. Dice the potatoes and pre-cook for 10 minutes.\n2. Slice the remaining vegetables and fry gently in oil, then salt.',
  h:'',
  a:'Avoid using iodised salt if possible.'},
'Kartoffelsuppe':{
  z:'1. Peel the potatoes, chop roughly and cook.\n2. Blend with oil and salt and season to taste.',
  h:'',
  a:''},
'Bananen Reisbrei':{
  z:'Cook the rice, mash the bananas and mix in.',
  h:'',
  a:''},
'Braune Linsen Eintopf mit Räuchertofu':{
  z:'1. Prepare the vegetables, then fry in a large pot until cooked through and lightly browned, then stir in the tomato paste and toast briefly.\n2. Add the lentils together with the potatoes, salt and bay leaf, bring to a boil and simmer until cooked through.\n3. Meanwhile, fry the tofu separately and keep ready as a topping, or stir in.',
  h:'Without tofu, the dish is soy-free.',
  a:''},
'Risotto mit Blumenkohl':{
  z:'1. Break the cauliflower into half florets, peel the garlic and fry with a little oil until golden. Add the garlic, steam with a little water until soft, then blend to a smooth puree and stir in the nutritional yeast.\n2. Finely dice the onions and bring a pot of stock to a boil. Saute the onions in a large pot until translucent. Add the risotto rice and heat with a little oil. Optionally deglaze with white wine. Gradually stir in the stock until the risotto rice is cooked.\n3. Stir the cauliflower mixture into the risotto, season and taste.',
  h:'',
  a:''},
'Süßkartoffel -Püree':{
  z:'1. Cook the sweet potatoes.\n2. Mash and stir in oil and salt.',
  h:'',
  a:''},
'Karotten-Ingwer-Suppe':{
  z:'Chop everything, cook until soft and blend. Season to taste.',
  h:'',
  a:''},
};

// Spatzbeilage has umlaut - match by original name
const originalNames={
  'Spätzlebeilage':'Spatzlebeilage',
};

let oatsCount=0;
data.recipes=data.recipes.map(r=>{
  const key=r.name;
  if(key==='Overnight Oats'){
    oatsCount++;
    if(oatsCount===2){
      return {...r,zubereitung_en:'Slice the bananas, mix everything together and leave in the fridge overnight.',hinweis_en:'',allergen_hinweis_en:''};
    }
  }
  // Try direct match first, then umlaut-mapped key
  const t2=tr[key]||tr[originalNames[key]];
  if(t2) return {...r,zubereitung_en:t2.z,hinweis_en:t2.h,allergen_hinweis_en:t2.a};
  return {...r,zubereitung_en:'',hinweis_en:'',allergen_hinweis_en:''};
});

fs.writeFileSync('standardbackup.json',JSON.stringify(data,null,2),'utf8');
const filled=data.recipes.filter(r=>r.zubereitung_en||r.hinweis_en||r.allergen_hinweis_en).length;
console.log('Done. Recipes with EN content:',filled,'of',data.recipes.length);
data.recipes.filter(r=>r.zubereitung_en||r.hinweis_en||r.allergen_hinweis_en).forEach(r=>console.log(' +',r.name));
